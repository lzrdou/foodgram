from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """Модель пользователя."""
    USER = "user"
    ADMIN = "admin"
    USER_ROLE = [
        (USER, USER),
        (ADMIN, ADMIN),
    ]

    username_validator = RegexValidator(
        regex=r'^[\w.@+-]',
        message=(
            'Неверный формат'
        )
    )

    email = models.EmailField(max_length=254, unique=True)
    username = models.CharField(
        max_length=150,
        validators=[username_validator, ],
        unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    password = models.CharField(max_length=150)
    role = models.CharField(
        choices=USER_ROLE,
        max_length=5,
        blank=True,
        null=True,
        default=USER
    )
    is_superuser = models.BooleanField(default=False)

    @property
    def is_user(self):
        return self.USER

    @property
    def is_admin(self):
        return self.role == self.ADMIN or self.is_staff

    class Meta:
        ordering = ("username",)
        verbose_name = "Пользователь"
        verbose_name_plural = 'Пользователи'


class Follow(models.Model):
    """Модель подписки на автора."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow'
            )
        ]
