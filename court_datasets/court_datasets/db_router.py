class DBRouter:
    def db_for_read(self, model, **hints):
        if model._meta.model_name in ["forumthread", "threadmessage"]:
            return "parser_db"
        elif model._meta.model_name in ["judge", "workhistory"]:
            return "judges_db"
        elif model._meta.model_name == "claimnote":
            return "default"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.model_name in ["forumthread", "threadmessage"]:
            return "parser_db"
        elif model._meta.model_name in ["judge", "workhistory"]:
            return "judges_db"
        elif model._meta.model_name == "claimnote":
            return "default"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == "datasets":
            if model_name == "claimnote":
                return db == "default"
            # Запрещаем миграции для внешних моделей в любой базе
            if model_name in ["forumthread", "threadmessage", "judge", "workhistory"]:
                return False
        return False