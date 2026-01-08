from django.shortcuts import render, get_object_or_404
from django.utils.timezone import now
from django.db.models import Q

from ..models import Article


def blog_list(request):
    articles = Article.objects.filter(
        is_published=True
    ).filter(
        Q(published_at__lte=now()) | Q(published_at__isnull=True)
    ).order_by("-published_at", "-created_at")

    return render(request, "tool/blog_list.html", {
        "articles": articles,
    })


def blog_detail(request, slug):
    article = get_object_or_404(
        Article.objects.filter(
            is_published=True
        ).filter(
            Q(published_at__lte=now()) | Q(published_at__isnull=True)
        ),
        slug=slug,
    )

    return render(request, "tool/blog_detail.html", {
        "article": article,
    })
