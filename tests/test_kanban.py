import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kanban import Problem, connect, operate


class KanbanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = connect(Path(self.temp.name) / 'test.sqlite3')
        self.alice = self.db.execute("INSERT INTO users(email,password) VALUES('alice@example.com','x')").lastrowid
        self.bob = self.db.execute("INSERT INTO users(email,password) VALUES('bob@example.com','x')").lastrowid
        self.carol = self.db.execute("INSERT INTO users(email,password) VALUES('carol@example.com','x')").lastrowid
        self.board = operate(self.db, self.alice, 'POST', ['boards'], {'name':'Website Relaunch'})
        self.bid = self.board['id']

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def op(self, user, method, tail, data=None):
        return operate(self.db, user, method, ['boards',str(self.bid)] + tail, data or {})

    def test_board_columns_and_card_order_persist(self):
        self.assertEqual([c['name'] for c in self.board['columns']], ['To Do','In Progress','Done'])
        first = self.board['columns'][0]['id']
        review = self.op(self.alice,'POST',['columns'],{'name':'Review'})['columns'][-1]['id']
        ids = [c['id'] for c in self.op(self.alice,'GET',[])['columns']]
        self.op(self.alice,'PATCH',['columns','order'],{'ids':[ids[0],ids[1],review,ids[2]]})
        self.op(self.alice,'PATCH',['columns',str(first)],{'name':'Backlog'})
        with self.assertRaisesRegex(Problem,'Card title is required'):
            self.op(self.alice,'POST',['cards'],{'column_id':first,'title':' '})
        for title in ['Write copy','Design hero image','Set up hosting']:
            self.op(self.alice,'POST',['cards'],{'column_id':first,'title':title})
        cards = self.op(self.alice,'GET',[])['columns'][0]['cards']
        self.op(self.alice,'PATCH',['cards','move'],{'card_id':cards[2]['id'],'column_id':first,'index':0})
        with self.assertRaisesRegex(Problem,'Move the cards'):
            self.op(self.alice,'DELETE',['columns',str(first)])
        self.db.commit(); self.db.close(); self.db=connect(Path(self.temp.name)/'test.sqlite3')
        saved=self.op(self.alice,'GET',[])
        self.assertEqual([c['name'] for c in saved['columns']],['Backlog','In Progress','Review','Done'])
        self.assertEqual([c['title'] for c in saved['columns'][0]['cards']],['Set up hosting','Write copy','Design hero image'])

    def test_member_permissions_and_board_isolation(self):
        self.op(self.alice,'POST',['members'],{'email':'bob@example.com'})
        first=self.board['columns'][0]['id']
        self.op(self.bob,'POST',['cards'],{'column_id':first,'title':'Bob task'})
        for tail,method,data in [([], 'PATCH', {'name':'Hijacked'}),(['columns'],'POST',{'name':'Blocked'}),(['members'],'POST',{'email':'carol@example.com'})]:
            with self.assertRaises(Problem) as cm:self.op(self.bob,method,tail,data)
            self.assertEqual(cm.exception.status,403)
        with self.assertRaises(Problem) as cm:self.op(self.carol,'GET',[])
        self.assertEqual(cm.exception.status,404)
        self.assertEqual(self.op(self.alice,'GET',[])['columns'][0]['cards'][0]['title'],'Bob task')

    def test_labels_belong_to_board(self):
        self.op(self.alice,'POST',['labels'],{'name':'Bug','color':'red'})
        other=operate(self.db,self.alice,'POST',['boards'],{'name':'Other'})
        self.assertEqual(other['labels'],[])

if __name__ == '__main__': unittest.main()
