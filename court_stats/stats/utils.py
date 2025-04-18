from datetime import timedelta

def format_timedelta_to_hours(hours):
    if hours == "Нет данных" or hours is None:
        return "Нет данных"
    days = int(hours // 24)
    hours_remainder = int(hours % 24)
    minutes = int((hours % 1) * 60)
    return f"{days} д. {hours_remainder} ч. {minutes} м."