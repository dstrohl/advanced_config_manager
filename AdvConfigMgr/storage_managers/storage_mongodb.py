import pymongo

from AdvConfigMgr.exceptions.config_exceptions import Error
from .config_storage import BaseConfigStorageManager


class ACMMongoStorageManagerConnectionError(Error):
    pass

class MongoStorageManager(BaseConfigStorageManager):
    """Read configuration from MongoDb.
        (requires pyMongo)

        each section will be stored as a separate document in the format of:

        section: section_name
        options: options dict

        configuration options include:

        connection: either a connection object or dictionary to use when calling MongoClient()
        database_name: the name for the database to use.
        collection_name: the name for the collection to use.
        database_authentication_dict: a dictionary pass to MongoClient.database.authenticate()
            (if None, authenticate will not be called.)

    """
    storage_type_name = 'Mongo Db Storage'
    storage_name = 'mongo'
    standard = True  #: True if this should be used for read_all/write_all ops

    _mongo_connection = None
    _mongo_database_name = None
    _mongo_collection_name = 'system_configuration_data'
    _mongo_database_authentication_dict = None
    _mongo_maintain_db_connection = False
    _mongo_collection = None

    def config(self, config_dict):
        """
        :param dict config_dict: a dictionary with storage specific configuration options., This is called after the
            storage manager is loaded.
        """
        super(MongoStorageManager, self).config(config_dict=config_dict)

        self._mongo_connection = config_dict.get('connection')
        self._mongo_database_name = config_dict.get('database_name')
        self._mongo_collection_name = config_dict.get('collection_name', self._mongo_collection_name)
        self._mongo_database_authentication_dict = config_dict.get('database_authentication_dict')
        self._mongo_maintain_db_connection = config_dict.get('maintain_db_connection', self._mongo_maintain_db_connection)

    @property
    def _mongo_conn(self):
        if not isinstance(self._mongo_connection, pymongo.MongoClient):
            if not isinstance(self._mongo_connection, dict):
                raise ACMMongoStorageManagerConnectionError('Connection parameter must be a MongoClient instance or a dict')
            self._mongo_connection = pymongo.MongoClient(**self._mongo_connection)

        if self._mongo_database_name is None:
            try:
                self._mongo_database_name = self._mongo_connection.get_default_database().name
            except pymongo.errors.ConfigurationError:
                raise ACMMongoStorageManagerConnectionError('No database information in uri or config')

        mongodb = self._mongo_connection[self._mongo_database_name]
        try:
            tmp_dbs = mongodb.collection_names()
        except pymongo.errors.OperationFailure:

            if self._mongo_database_authentication_dict is None:
                raise
            else:
                mongodb.authenticate(**self._mongo_database_authentication_dict)
        return self._mongo_connection

    @property
    def _mongo_db(self):
        if self._mongo_collection is None:
            self._mongo_collection = self._mongo_conn[self._mongo_database_name][self._mongo_collection_name]
        return self._mongo_collection

    def _mongo_close(self):
        # self._mongo_conn.fsync()
        if not self._mongo_maintain_db_connection:
            self._mongo_conn.close()

    def read(self, section_name=None, storage_name=storage_name, **kwargs):
        """
        will take a dictionary and save it to the system
        :param dict_in:
        :param storage_name:
        :return:
        """
        if isinstance(section_name, str):
            section_name = [section_name]
        section_count = 0
        option_count = 0
        tmp_data = {}

        mdb_cursor = self._mongo_db.find()

        for section in mdb_cursor:
            if section_name is None or section in section_name:
                section_count += 1
                # tmp_sec = self._mongo_db.find_one({'section': section})
                tmp_data[section['section']] = section['options']
                option_count += len(section['options'])

        self.last_option_count = option_count
        self.last_section_count = section_count
        self._save_dict(tmp_data, section_name, storage_name)

        self._mongo_close()
        return self.last_section_count, self.last_option_count

    def write(self, section_name=None, storage_name=storage_name, **kwargs):
        """
        will return a dictionary from the system
        :param storage_name:
        :return:
        """
        self.data = self._get_dict(section_name, storage_name)

        section_count = 0
        option_count = 0

        for section, options in self.data.items():
            tmp_dict = {'section': section, 'options': options}
            section_count += 1
            option_count += len(options)
            self._mongo_db.replace_one({'section': section}, tmp_dict, upsert=True)

        self.last_option_count = option_count
        self.last_section_count = section_count
        self._mongo_close()
        return self.last_section_count, self.last_option_count
