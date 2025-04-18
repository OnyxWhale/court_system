from django.db import models
from django.utils import timezone

class ForumThreadLink1(models.Model):
    url = models.URLField(unique=True, verbose_name="URL треда")
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    prefix = models.CharField(max_length=50, blank=True, verbose_name="Префикс")
    created_at = models.DateTimeField(verbose_name="Дата создания")
    updated_at = models.DateTimeField(verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Тред форума (Верховный суд)"
        verbose_name_plural = "Треды форума (Верховный суд)"

    def __str__(self):
        return self.title

class ThreadMessageLink1(models.Model):
    thread = models.ForeignKey(ForumThreadLink1, on_delete=models.CASCADE, verbose_name="Тред")
    url = models.URLField(verbose_name="URL сообщения")
    author = models.CharField(max_length=100, verbose_name="Автор")
    content = models.TextField(verbose_name="Содержимое")
    posted_at = models.DateTimeField(verbose_name="Дата публикации")

    class Meta:
        verbose_name = "Сообщение треда (Верховный суд)"
        verbose_name_plural = "Сообщения тредов (Верховный суд)"

    def __str__(self):
        return f"{self.author} в {self.thread.title}"

class ForumThreadLink2(models.Model):
    url = models.URLField(unique=True, verbose_name="URL треда")
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    prefix = models.CharField(max_length=50, blank=True, verbose_name="Префикс")
    created_at = models.DateTimeField(verbose_name="Дата создания")
    updated_at = models.DateTimeField(verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Тред форума (Федеральный суд)"
        verbose_name_plural = "Треды форума (Федеральный суд)"

    def __str__(self):
        return self.title

class ThreadMessageLink2(models.Model):
    thread = models.ForeignKey(ForumThreadLink2, on_delete=models.CASCADE, verbose_name="Тред")
    url = models.URLField(verbose_name="URL сообщения")
    author = models.CharField(max_length=100, verbose_name="Автор")
    content = models.TextField(verbose_name="Содержимое")
    posted_at = models.DateTimeField(verbose_name="Дата публикации")

    class Meta:
        verbose_name = "Сообщение треда (Федеральный суд)"
        verbose_name_plural = "Сообщения тредов (Федеральный суд)"

    def __str__(self):
        return f"{self.author} в {self.thread.title}"

class ForumThreadLink3(models.Model):
    url = models.URLField(unique=True, verbose_name="URL треда")
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    prefix = models.CharField(max_length=50, blank=True, verbose_name="Префикс")
    created_at = models.DateTimeField(verbose_name="Дата создания")
    updated_at = models.DateTimeField(verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Тред форума (Реабилитации)"
        verbose_name_plural = "Треды форума (Реабилитации)"

    def __str__(self):
        return self.title

class ThreadMessageLink3(models.Model):
    thread = models.ForeignKey(ForumThreadLink3, on_delete=models.CASCADE, verbose_name="Тред")
    url = models.URLField(verbose_name="URL сообщения")
    author = models.CharField(max_length=100, verbose_name="Автор")
    content = models.TextField(verbose_name="Содержимое")
    posted_at = models.DateTimeField(verbose_name="Дата публикации")

    class Meta:
        verbose_name = "Сообщение треда (Реабилитации)"
        verbose_name_plural = "Сообщения тредов (Реабилитации)"

    def __str__(self):
        return f"{self.author} в {self.thread.title}"

class ParseProgress(models.Model):
    LINK_CHOICES = (
        ('link1', 'Верховный суд'),
        ('link2', 'Федеральный суд'),
        ('link3', 'Реабилитации'),
    )
    link_type = models.CharField(max_length=10, choices=LINK_CHOICES, verbose_name="Тип ссылки")
    processed_threads = models.IntegerField(default=0, verbose_name="Обработано тредов")
    total_threads = models.IntegerField(default=0, verbose_name="Всего тредов")
    progress = models.FloatField(default=0.0, verbose_name="Прогресс (%)")
    task_id = models.CharField(max_length=255, null=True, blank=True, verbose_name="ID задачи")
    status = models.CharField(max_length=50, default="pending", verbose_name="Статус")

    class Meta:
        verbose_name = "Прогресс парсинга"
        verbose_name_plural = "Прогресс парсинга"
        unique_together = ('link_type',)

    def __str__(self):
        return f"{self.get_link_type_display()}: {self.status} ({self.progress}%)"