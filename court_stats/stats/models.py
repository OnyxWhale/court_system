from django.db import models
from django.utils import timezone

# Неуправляемые модели для parser_db
class ForumThreadLink1(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    url = models.URLField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    prefix = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "parser_forumthreadlink1"
        app_label = "stats"
        verbose_name = "Тред Верховного суда"

class ThreadMessageLink1(models.Model):
    id = models.AutoField(primary_key=True)
    thread = models.ForeignKey(ForumThreadLink1, on_delete=models.CASCADE, related_name="threadmessagelink1_set")
    author = models.CharField(max_length=100)
    posted_at = models.DateTimeField()
    content = models.TextField()
    url = models.URLField()

    class Meta:
        managed = False
        db_table = "parser_threadmessagelink1"
        app_label = "stats"
        verbose_name = "Сообщение Верховного суда"

class ForumThreadLink2(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    url = models.URLField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    prefix = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "parser_forumthreadlink2"
        app_label = "stats"
        verbose_name = "Тред Федерального суда"

class ThreadMessageLink2(models.Model):
    id = models.AutoField(primary_key=True)
    thread = models.ForeignKey(ForumThreadLink2, on_delete=models.CASCADE, related_name="threadmessagelink2_set")
    author = models.CharField(max_length=100)
    posted_at = models.DateTimeField()
    content = models.TextField()
    url = models.URLField()

    class Meta:
        managed = False
        db_table = "parser_threadmessagelink2"
        app_label = "stats"
        verbose_name = "Сообщение Федерального суда"

class ForumThreadLink3(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    url = models.URLField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    prefix = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "parser_forumthreadlink3"
        app_label = "stats"
        verbose_name = "Тред Реабилитации"

class ThreadMessageLink3(models.Model):
    id = models.AutoField(primary_key=True)
    thread = models.ForeignKey(ForumThreadLink3, on_delete=models.CASCADE, related_name="threadmessagelink3_set")
    author = models.CharField(max_length=100)
    posted_at = models.DateTimeField()
    content = models.TextField()
    url = models.URLField()

    class Meta:
        managed = False
        db_table = "parser_threadmessagelink3"
        app_label = "stats"
        verbose_name = "Сообщение Реабилитации"

# Неуправляемые модели для judges_db
class Judge(models.Model):
    id = models.IntegerField(primary_key=True)
    full_name = models.CharField(max_length=255)
    forum_account = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "judges_judge"
        app_label = "stats"

class WorkHistory(models.Model):
    id = models.AutoField(primary_key=True)
    judge = models.ForeignKey(Judge, on_delete=models.CASCADE, related_name="workhistory_set")
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "judges_workhistory"
        app_label = "stats"

# Управляемая модель для локальной базы
class StatSummary(models.Model):
    source = models.CharField(max_length=10, choices=[
        ('link1', 'Верховный суд'),
        ('link2', 'Федеральный суд'),
        ('link3', 'Реабилитации'),
    ])
    total_threads = models.IntegerField(default=0)
    prefix_counts = models.JSONField(default=dict)
    avg_first_response = models.FloatField(null=True, blank=True)
    median_first_response = models.FloatField(null=True, blank=True)
    avg_court_time = models.FloatField(null=True, blank=True)
    median_court_time = models.FloatField(null=True, blank=True)
    judge_stats = models.JSONField(default=dict)
    threads_by_date = models.JSONField(default=dict)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Сводка статистики"
        verbose_name_plural = "Сводки статистики"
        app_label = "stats"