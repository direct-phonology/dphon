"""Tests for the text reuse module."""

from unittest import TestCase, skip

import spacy
from dphon.reuse import MatchGraph
from spacy.tokens import Doc
from dphon.extend import LevenshteinExtender


class TestMatchGraph(TestCase):
    """Test the MatchGraph class."""

    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        """register spaCy extensions"""
        Doc.set_extension("title", default="")

    @classmethod
    def tearDown(cls) -> None:
        """unregister spaCy extensions to prevent collisions"""
        Doc.remove_extension("title")

    def setUp(self) -> None:
        """create a spaCy pipeline and match graph for testing"""
        self.nlp = spacy.blank(
            "zh", meta={"tokenizer": {"config": {"use_jieba": False}}})
        self.G = MatchGraph()
        # doc1 = self.nlp.make_doc("與朋友交言而有信雖曰未學吾必謂之學矣")
        # doc2 = self.nlp.make_doc("與朋友交言而有信雖曰已學吾必謂之未也")
        # doc3 = self.nlp.make_doc("與朋友交言而有信雖未讀書吾亦謂之學矣")

    @skip("todo")
    def test_combine(self) -> None:
        """combine should combine overlapping matches"""
        doc1 = self.nlp.make_doc("與朋友交言而有信雖曰未學吾")
        doc2 = self.nlp.make_doc("與朋友交言而有信雖曰已學吾")
        doc3 = self.nlp.make_doc("與朋友交言而有信雖未讀書吾")
        self.G.add_docs([("論語·學而", doc1),
                         ("藝文類聚·錢", doc2),
                         ("顏氏家訓·勉學", doc3)])
        self.G.add_matches([
            ("論語·學而", "藝文類聚·錢", doc1[0:4], doc2[0:4]),         # 與朋友交
            ("論語·學而", "藝文類聚·錢", doc1[4:8], doc2[4:8]),         # 言而有信
            ("論語·學而", "顏氏家訓·勉學", doc1[0:4], doc3[0:4]),       # 與朋友交
            ("論語·學而", "顏氏家訓·勉學", doc1[4:8], doc3[4:8]),       # 言而有信
            ("藝文類聚·錢", "顏氏家訓·勉學", doc2[0:4], doc3[0:4]),     # 與朋友交
            ("藝文類聚·錢", "顏氏家訓·勉學", doc2[4:8], doc3[4:8]),     # 言而有信
        ])
        extender = LevenshteinExtender(threshold=0.8, len_limit=50)
        self.G.extend(extender)
        self.assertTrue(True)

    @skip("todo")
    def test_extend(self) -> None:
        """extend should reduce graph to maximal matches only"""
        doc1 = self.nlp.make_doc("與朋友交言而有信雖曰未學吾")
        doc2 = self.nlp.make_doc("與朋友交言而有信雖曰已學吾")
        doc3 = self.nlp.make_doc("與朋友交言而有信雖未讀書吾")
        self.G.add_docs([("論語·學而", doc1),
                         ("藝文類聚·錢", doc2),
                         ("顏氏家訓·勉學", doc3)])
        self.G.add_matches([
            ("論語·學而", "藝文類聚·錢", doc1[0:4], doc2[0:4]),         # 與朋友交
            ("論語·學而", "藝文類聚·錢", doc1[4:8], doc2[4:8]),         # 言而有信
            ("論語·學而", "顏氏家訓·勉學", doc1[0:4], doc3[0:4]),       # 與朋友交
            ("論語·學而", "顏氏家訓·勉學", doc1[4:8], doc3[4:8]),       # 言而有信
            ("藝文類聚·錢", "顏氏家訓·勉學", doc2[0:4], doc3[0:4]),     # 與朋友交
            ("藝文類聚·錢", "顏氏家訓·勉學", doc2[4:8], doc3[4:8]),     # 言而有信
        ])
        extender = LevenshteinExtender(threshold=0.8, len_limit=50)
        self.G.extend(extender)
        self.assertTrue(True)

    @skip("todo")
    def test_filter(self) -> None:
        return
