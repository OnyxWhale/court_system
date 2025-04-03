from django.db import models
from django.utils import timezone

class ForumThread(models.Model):
    url = models.URLField(unique=True, verbose_name="URL треда")
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    prefix = models.CharField(max_length=50, blank=True, verbose_name="Префикс")
    created_at = models.DateTimeField(verbose_name="Дата создания")
    updated_at = models.DateTimeField(verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Тред форума"
        verbose_name_plural = "Треды форума"

    def __str__(self):
        return self.title

class ThreadMessage(models.Model):
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE, verbose_name="Тред")
    url = models.URLField(verbose_name="URL сообщения")
    author = models.CharField(max_length=100, verbose_name="Автор")
    content = models.TextField(verbose_name="Содержимое")
    posted_at = models.DateTimeField(verbose_name="Дата публикации")

    class Meta:
        verbose_name = "Сообщение треда"
        verbose_name_plural = "Сообщения тредов"

    def __str__(self):
        return f"{self.author} в {self.thread.title}"

class ParseProgress(models.Model):
    processed_threads = models.IntegerField(default=0, verbose_name="Обработано тредов")
    total_threads = models.IntegerField(default=0, verbose_name="Всего тредов")
    progress = models.FloatField(default=0.0, verbose_name="Прогресс (%)")
    task_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=50, default="pending", verbose_name="Статус")

    class Meta:
        verbose_name = "Прогресс парсинга"
        verbose_name_plural = "Прогресс парсинга"

    def __str__(self):
        return f"{self.status} ({self.progress}%)"