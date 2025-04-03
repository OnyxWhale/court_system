from django.db import models

# Неуправляемые модели (заглушки для внешних таблиц)
class ForumThread(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    url = models.URLField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)
    prefix = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "parser_forumthread"
        app_label = "datasets"

    def __str__(self):
        return self.title

class ThreadMessage(models.Model):
    id = models.AutoField(primary_key=True)
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE)
    author = models.CharField(max_length=100)
    posted_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "parser_threadmessage"
        app_label = "datasets"

class Judge(models.Model):
    id = models.IntegerField(primary_key=True)
    full_name = models.CharField(max_length=255)
    forum_account = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "judges_judge"
        app_label = "datasets"

class WorkHistory(models.Model):
    id = models.AutoField(primary_key=True)
    judge = models.ForeignKey(Judge, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "judges_workhistory"
        app_label = "datasets"

class ClaimNote(models.Model):
    thread_id = models.IntegerField(unique=True, verbose_name="ID треда")
    note = models.TextField(blank=True, null=True, verbose_name="Примечание")

    class Meta:
        verbose_name = "Примечание к иску"
        verbose_name_plural = "Примечания к искам"
        app_label = "datasets"

    def __str__(self):
        return f"Примечание к треду {self.thread_id}"