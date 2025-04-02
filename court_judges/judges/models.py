from django.db import models
from django.utils import timezone

class Judge(models.Model):
    full_name = models.CharField(max_length=255, unique=True, verbose_name="Полное имя")
    forum_account = models.CharField(max_length=100, unique=True, verbose_name="Форумный аккаунт")
    discord_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID Discord")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail")
    telegram = models.CharField(max_length=100, blank=True, null=True, verbose_name="Телеграм")
    additional_info = models.TextField(blank=True, null=True, verbose_name="Дополнительно")

    class Meta:
        verbose_name = "Судья"
        verbose_name_plural = "Судьи"
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name

    def is_currently_working(self):
        current_date = timezone.now()
        for history in self.workhistory_set.all():
            if history.start_date <= current_date and (history.end_date is None or history.end_date >= current_date):
                return True
        return False

class WorkHistory(models.Model):
    judge = models.ForeignKey(Judge, on_delete=models.CASCADE, related_name="workhistory_set", verbose_name="Судья")
    start_date = models.DateTimeField(verbose_name="Дата принятия")
    end_date = models.DateTimeField(blank=True, null=True, verbose_name="Дата увольнения")

    class Meta:
        verbose_name = "История работы"
        verbose_name_plural = "История работы"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.judge.full_name}: {self.start_date} - {self.end_date or 'по настоящее время'}"