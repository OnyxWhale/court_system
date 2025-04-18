class DBRouter:
    def db_for_read(self, model, **hints):
        if model._meta.model_name in [
            "forumthreadlink1", "threadmessagelink1",
            "forumthreadlink2", "threadmessagelink2",
            "forumthreadlink3", "threadmessagelink3"
        ]:
            return "parser_db"
        elif model._meta.model_name in ["judge", "workhistory"]:
            return "judges_db"
        elif model._meta.model_name == "statsummary":
            return "default"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.model_name in [
            "forumthreadlink1", "threadmessagelink1",
            "forumthreadlink2", "threadmessagelink2",
            "forumthreadlink3", "threadmessagelink3"
        ]:
            return "parser_db"
        elif model._meta.model_name in ["judge", "workhistory"]:
            return "judges_db"
        elif model._meta.model_name == "statsummary":
            return "default"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == "stats":
            if model_name == "statsummary":
                return db == "default"
            if model_name in [
                "forumthreadlink1", "threadmessagelink1",
                "forumthreadlink2", "threadmessagelink2",
                "forumthreadlink3", "threadmessagelink3",
                "judge", "workhistory"
            ]:
                return False
        return False