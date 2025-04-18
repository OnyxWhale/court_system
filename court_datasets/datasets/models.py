from django.db import models

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
        app_label = "datasets"
        verbose_name = "Тред Верховного суда"
        verbose_name_plural = "Треды Верховного суда"

    def __str__(self):
        return self.title

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
        app_label = "datasets"
        verbose_name = "Сообщение Верховного суда"
        verbose_name_plural = "Сообщения Верховного суда"

    def __str__(self):
        return f"{self.author} в {self.thread.title}"

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
        app_label = "datasets"
        verbose_name = "Тред Федерального суда"
        verbose_name_plural = "Треды Федерального суда"

    def __str__(self):
        return self.title

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
        app_label = "datasets"
        verbose_name = "Сообщение Федерального суда"
        verbose_name_plural = "Сообщения Федерального суда"

    def __str__(self):
        return f"{self.author} в {self.thread.title}"

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
        app_label = "datasets"
        verbose_name = "Тред Реабилитации"
        verbose_name_plural = "Треды Реабилитации"

    def __str__(self):
        return self.title

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
        app_label = "datasets"
        verbose_name = "Сообщение Реабилитации"
        verbose_name_plural = "Сообщения Реабилитации"

    def __str__(self):
        return f"{self.author} в {self.thread.title}"

# Неуправляемые модели для judges_db
class Judge(models.Model):
    id = models.IntegerField(primary_key=True)
    full_name = models.CharField(max_length=255)
    forum_account = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "judges_judge"
        app_label = "datasets"

    def __str__(self):
        return self.full_name

class WorkHistory(models.Model):
    id = models.AutoField(primary_key=True)
    judge = models.ForeignKey(Judge, on_delete=models.CASCADE, related_name="workhistory_set")
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "judges_workhistory"
        app_label = "datasets"

# Управляемая модель для локальной базы
class ClaimNote(models.Model):
    thread_id = models.IntegerField(unique=True, verbose_name="ID треда")
    note = models.TextField(blank=True, null=True, verbose_name="Примечание")
    source = models.CharField(max_length=10, choices=[
        ('link1', 'Верховный суд'),
        ('link2', 'Федеральный суд'),
        ('link3', 'Реабилитации'),
    ], default='link2', verbose_name="Источник")

    class Meta:
        verbose_name = "Примечание к иску"
        verbose_name_plural = "Примечания к искам"
        app_label = "datasets"

    def __str__(self):
        return f"Примечание к треду {self.thread_id} ({self.source})"