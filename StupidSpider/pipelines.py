# -*- coding: utf-8 -*-
import psycopg2
import psycopg2.extras

from twisted.enterprise import adbapi
from scrapy.exporters import JsonItemExporter
from scrapy.pipelines.images import ImagesPipeline


# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

class StupidspiderPipeline(object):
    def process_item(self, item, spider):
        return item


class ArticleImgPipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        # TODO if 'front_image_url' in item:
        for ok, d in results:
            if ok:
                item['front_img_path'] = d['path']

        return item


class JsonExporterPipeline:
    def __init__(self):
        self.file = open('article.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf8', ensure_ascii=False)

        self.exporter.start_exporting()

    def process_item(self, item, spider):
        self.exporter.export_item(item)

        return item

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()


class PostgreSQLTwistedPipeline:
    def __init__(self, db_pool):
        self.db_pool = db_pool

    @classmethod
    def from_settings(cls, settings):
        db_params = dict(
            host=settings['POSTGRESQL_HOST'],
            port=settings['POSTGRESQL_PORT'],
            user=settings['POSTGRESQL_USER'],
            password=settings['POSTGRESQL_PASSWORD'],
            database=settings['POSTGRESQL_SCRAPY_DATABASE'],
            cursor_factory=psycopg2.extras.DictCursor
        )

        db_pool = adbapi.ConnectionPool('psycopg2', **db_params)

        return cls(db_pool)

    def process_item(self, item, spider):
        querry = self.db_pool.runInteraction(self.insert, item)
        querry.addErrback(self.handler_err, item, spider)

    def handler_err(self, failure, item, spider):
        print(failure, item, spider)

    def insert(self, cursor, item):
        sql, params = item.insert_sql_with_params()
        cursor.execute(sql, params)
