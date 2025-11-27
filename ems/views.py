from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
import json
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Category, Event, Outcome
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout

def user_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  # creates session automatically
            return redirect("home")  # your home page
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "ems/login.html")

def user_logout(request):
    logout(request)  # clears session
    return redirect("login")

def category_list(request):
    """Display all available categories."""
    categories = Category.objects.all()
    return render(request, 'ems/category_list.html', {'categories': categories})

@login_required(login_url='login')
def home(request):
    logs = Event.objects.filter(user=request.user).prefetch_related('outcome_entries').order_by('start_date')

    now = timezone.now()  # this is datetime.datetime

    logs_list = []
    for event in logs:
        # count related outcomes
        outcome_count = event.outcome_entries.count()

        # ensure start_date and end_date are datetime.datetime
        start_dt = event.start_date
        end_dt = event.end_date

        # flags for frontend
        is_upcoming = end_dt and end_dt >= now
        is_pending = end_dt and end_dt < now and outcome_count == 0

        logs_list.append({
            'id': event.id,
            'name': event.name or "Unnamed",
            'project_type': event.project_type or "other",
            'description': event.description or "",
            'organizer': event.organizer or "",
            'start_date': start_dt.strftime("%Y-%m-%d") if start_dt else "",
            'end_date': end_dt.strftime("%Y-%m-%d") if end_dt else "",
            'outcome_count': outcome_count,
            'is_upcoming': is_upcoming,
            'is_pending': is_pending,
        })

    return render(request, 'ems/home.html', {
        'logs_json': json.dumps(logs_list)
    })



@login_required(login_url='login')
def create_category(request):
    """Add a new category (programme)."""
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Category.objects.create(name=name)
            messages.success(request, f'Programme "{name}" added successfully.')
        else:
            messages.error(request, "Programme name cannot be empty.")
        return redirect('event_timeline')
    return render(request, 'ems/create_category.html')


@login_required(login_url='login')
def delete_category(request, category_id):
    """Delete a category only if it has no events."""
    category = get_object_or_404(Category, pk=category_id)
    if category.event_set.exists():
        messages.error(request, "You cannot delete this programme as it contains events.")
    else:
        category.delete()
        messages.success(request, "Programme deleted successfully.")
    return redirect('event_timeline')


@login_required(login_url='login')
def category_events(request, category_id):
    """Display all events under a specific category."""
    category = get_object_or_404(Category, pk=category_id)
    events = category.event_set.all().order_by('-start_date')
    return render(request, 'ems/category_events.html', {'category': category, 'events': events})


# ------------------------------
# EVENT VIEWS
# ------------------------------
@login_required(login_url='login')
def create_event(request):
    """Create a new event."""
    categories = Category.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        project_type = request.POST.get('project_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        description = request.POST.get('description')
        location = request.POST.get('location')
        organizer = request.POST.get('organizer')
        participants = request.POST.get('participants')

        category = get_object_or_404(Category, pk=category_id)

        Event.objects.create(
            user=request.user,
            name=name,
            category=category,
            project_type=project_type,
            start_date=start_date,
            end_date=end_date,
            description=description,
            location=location,
            organizer=organizer,
            participants=participants,
        )

        messages.success(request, f'Event "{name}" created successfully.')
        return redirect('event_timeline')

    return render(request, 'ems/create_event.html', {'categories': categories})


@login_required(login_url='login')
def update_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    categories = Category.objects.all()  # <--- add this

    if request.method == 'POST':
        event.name = request.POST.get('name')
        event.category = get_object_or_404(Category, pk=request.POST.get('category'))
        event.project_type = request.POST.get('project_type')
        event.start_date = request.POST.get('start_date')
        event.end_date = request.POST.get('end_date')
        event.description = request.POST.get('description')
        event.location = request.POST.get('location')
        event.organizer = request.POST.get('organizer')
        event.participants = request.POST.get('participants', '')
        event.save()
        messages.success(request, f'Event "{event.name}" updated successfully.')
        return redirect('event_timeline')

    return render(request, 'ems/update_event.html', {
        'event': event,
        'categories': categories  # <--- pass categories here
    })


@login_required(login_url='login')
def delete_event(request, event_id):
    """Delete an event."""
    if request.method == 'POST':
        event = get_object_or_404(Event, pk=event_id)
        event.delete()
        messages.success(request, "Event deleted successfully.")
    return redirect('event_timeline')


# ------------------------------
# ANALYTICS / VISUALIZATION
# ------------------------------
@login_required(login_url='login')
def event_chart(request):
    """Display pending (upcoming or ongoing) events by category as a bar chart."""
    now = timezone.now()
    pending_counts_qs = (
        Event.objects.filter(end_date__gt=now)
        .values('category__name')
        .annotate(count=Count('id'))
        .order_by('category__name')
    )
    pending_counts = {item['category__name']: item['count'] for item in pending_counts_qs}

    return render(request, 'ems/event_chart.html', {'pending_counts': pending_counts})


@login_required(login_url='login')
def event_time(request):
    # Fetch all events for the current user
    events = Event.objects.filter(user=request.user).order_by('start_date')

    logs_list = []
    for event in events:
        # Count related outcome entries for this event
        outcome_count = event.outcome_entries.count()

        logs_list.append({
            'id': event.id,
            'name': event.name or "Unnamed",
            'project_type': event.project_type or "general",
            'start_date': event.start_date.strftime("%Y-%m-%d") if event.start_date else "",
            'end_date': event.end_date.strftime("%Y-%m-%d") if event.end_date else "",
            'outcome_entries': outcome_count
        })

    # Handle case with no events
    if not logs_list:
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        logs_list.append({
            "id": "placeholder",
            "name": "No Activities Logged Yet",
            "project_type": "placeholder",
            "start_date": week_start.isoformat(),
            "end_date": week_end.isoformat(),
            "outcome_entries": 0
        })

    return render(request, 'ems/event_timeline.html', {
        'logs_json': json.dumps(logs_list)
    })

    # If no events exist, add a placeholder
    if not logs_list:
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        logs_list.append({
            "id": "placeholder",
            "name": "No Activities Logged Yet",
            "project_type": "placeholder",
            "start_date": week_start.isoformat(),
            "end_date": week_end.isoformat(),
            "description": "",
            "organizer": "",
            "outcomes_entries": []
        })

    return render(request, 'ems/event_timeline.html', {
        'logs_json': json.dumps(logs_list)
    })

@login_required(login_url='login')
def outcome_list_create(request, event_id):
    event = get_object_or_404(Event, pk=event_id, user=request.user)

    if request.method == "GET":
        outcomes = list(event.outcome_entries.order_by("-created_at").values(
            "id", "start_date", "end_date", "duration", "rappo", "topics", "outcome_text", "recommendation"
        ))
        return JsonResponse({"outcomes": outcomes})

    elif request.method == "POST":
        # Get fields
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        duration = request.POST.get("duration")
        rappo = request.POST.get("rappo")
        topics = request.POST.get("topics")
        outcome_text = request.POST.get("outcome_text")
        recommendation = request.POST.get("recommendation")

        Outcome.objects.create(
            event=event,
            start_date=start_date,
            end_date=end_date,
            duration=duration,
            rappo=rappo,
            topics=topics,
            outcome_text=outcome_text,
            recommendation=recommendation
        )
        return JsonResponse({"status": "success"})

    return JsonResponse({"error": "Invalid method"}, status=405)

@login_required(login_url='login')
def event_timeline(request):
    """Render timeline with events and related outcomes."""
    #events = Event.objects.filter(user=request.user).order_by('start_date')
    events = Event.objects.all().order_by('start_date')

    logs_list = []
    for event in events:
        # Get all outcomes related to this event
        outcomes = event.outcome_entries.all().order_by('-start_date')
        outcome_entries = [
            {
                'outcome_text': o.outcome_text,
                'recommendation': o.recommendation or '',
                'start_date': o.start_date.strftime("%Y-%m-%d") if o.start_date else '',
                'end_date': o.end_date.strftime("%Y-%m-%d") if o.end_date else ''
            } 
            for o in outcomes
        ]

        logs_list.append({
            'id': str(event.id),
            'name': event.name or "Unnamed",
            'project_type': event.project_type or 'other',
            'start_date': event.start_date.strftime("%Y-%m-%d") if event.start_date else '',
            'end_date': event.end_date.strftime("%Y-%m-%d") if event.end_date else '',
            'description': event.description or '',
            'organizer': event.organizer or '',
            'outcomes_entries': outcome_entries  # <-- use Outcome model instead of flat field
        })

    # Placeholder if no events exist
    if not logs_list:
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        logs_list.append({
            "id": "placeholder",
            "name": "No Activities Logged Yet",
            "project_type": "placeholder",
            "start_date": week_start.isoformat(),
            "end_date": week_end.isoformat(),
            "description": "",
            "organizer": "",
            "outcomes_entries": []
        })

    return render(request, 'ems/event_timeline.html', {
        'logs_json': json.dumps(logs_list)
    })


@login_required(login_url='login')
def outcome_list(request, event_id):
    """Return all outcomes for an event (GET) or create new outcome (POST)."""
    event = get_object_or_404(Event, pk=event_id, user=request.user)

    if request.method == "GET":
        outcomes = list(event.outcome_entries.order_by("-created_at").values(
            "id", "start_date", "end_date", "duration", "rappo",
            "topics", "outcome_text", "recommendation"
        ))
        return JsonResponse({"outcomes": outcomes})

    elif request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        duration = request.POST.get("duration")
        rappo = request.POST.get("rappo")
        topics = request.POST.get("topics")
        outcome_text = request.POST.get("outcome_text")
        recommendation = request.POST.get("recommendation")

        outcome = Outcome.objects.create(
            event=event,
            start_date=start_date,
            end_date=end_date,
            duration=duration,
            rappo=rappo,
            topics=topics,
            outcome_text=outcome_text,
            recommendation=recommendation
        )
        return JsonResponse({"status": "success", "id": outcome.id})

    return JsonResponse({"error": "Invalid method"}, status=405)


@login_required(login_url='login')
def outcome_detail(request, outcome_id):
    """Return a single outcome for editing."""
    outcome = get_object_or_404(Outcome, pk=outcome_id, event__user=request.user)
    data = {
        "id": outcome.id,
        "start_date": outcome.start_date,
        "end_date": outcome.end_date,
        "duration": outcome.duration,
        "rappo": outcome.rappo,
        "topics": outcome.topics,
        "outcome_text": outcome.outcome_text,
        "recommendation": outcome.recommendation,
    }
    return JsonResponse(data)


@login_required(login_url='login')
def outcome_update(request, outcome_id):
    """Update an existing outcome."""
    outcome = get_object_or_404(Outcome, pk=outcome_id)

    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    outcome.start_date = request.POST.get("start_date")
    outcome.end_date = request.POST.get("end_date")
    outcome.duration = request.POST.get("duration")
    outcome.rappo = request.POST.get("rappo")
    outcome.topics = request.POST.get("topics")
    outcome.outcome_text = request.POST.get("outcome_text")
    outcome.recommendation = request.POST.get("recommendation")
    outcome.save()

    return JsonResponse({"status": "success"})



@login_required(login_url='login')
def outcome_list_create(request, event_id):
    """List outcomes or create new outcome"""
    event = get_object_or_404(Event, pk=event_id, user=request.user)

    if request.method == "GET":
        outcomes = list(event.outcome_entries.order_by("-created_at").values(
            "id", "start_date", "end_date", "duration", "rappo",
            "topics", "outcome_text", "recommendation"
        ))
        return JsonResponse({"outcomes": outcomes})

    elif request.method == "POST":
        outcome = Outcome.objects.create(
            event=event,
            start_date=request.POST.get("start_date"),
            end_date=request.POST.get("end_date"),
            duration=request.POST.get("duration"),
            rappo=request.POST.get("rappo"),
            topics=request.POST.get("topics"),
            outcome_text=request.POST.get("outcome_text"),
            recommendation=request.POST.get("recommendation")
        )
        return JsonResponse({"status": "success", "id": outcome.id})
