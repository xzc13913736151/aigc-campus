from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AssistantActionProposal, AssistantMessage, AssistantSession
from .orchestrator import build_assistant_presentation, plan_assistant_turn
from .serializers import (
    AssistantActionExecuteResponseSerializer,
    AssistantActionProposalSerializer,
    AssistantMessageCreateSerializer,
    AssistantMessageSerializer,
    AssistantSessionCreateSerializer,
    AssistantSessionSerializer,
)
from .services import default_session_title
from .skills import execute_action


class AssistantSessionListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AssistantSession.objects.filter(user=self.request.user).prefetch_related("messages")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AssistantSessionCreateSerializer
        return AssistantSessionSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = AssistantSessionSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = AssistantSession.objects.create(
            user=request.user,
            title=serializer.validated_data.get("title") or default_session_title(serializer.validated_data.get("page_type", AssistantSession.PageType.GENERAL)),
            page_type=serializer.validated_data.get("page_type", AssistantSession.PageType.GENERAL),
            context_path=serializer.validated_data.get("context_path", ""),
            context_target_type=serializer.validated_data.get("context_target_type", ""),
            context_target_id=serializer.validated_data.get("context_target_id", ""),
        )
        return Response(AssistantSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class AssistantMessageListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssistantMessageSerializer

    def get_session(self):
        return get_object_or_404(AssistantSession.objects.prefetch_related("messages"), pk=self.kwargs["session_id"], user=self.request.user)

    def get_queryset(self):
        return AssistantMessage.objects.filter(session=self.get_session())

    def list(self, request, *args, **kwargs):
        serializer = AssistantMessageSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        session = self.get_session()
        serializer = AssistantMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        previous_messages = list(session.messages.order_by("-created_at")[:8])
        previous_messages.reverse()
        AssistantActionProposal.objects.filter(
            session=session,
            user=request.user,
            status=AssistantActionProposal.Status.PENDING,
            expires_at__gt=timezone.now(),
        ).update(status=AssistantActionProposal.Status.DISMISSED, updated_at=timezone.now())

        user_message = AssistantMessage.objects.create(
            session=session,
            role=AssistantMessage.Role.USER,
            body=serializer.validated_data["body"],
        )
        previous_messages.append(user_message)
        assistant_body, proposal_payloads, next_state = plan_assistant_turn(
            request.user,
            session,
            serializer.validated_data["body"],
            previous_messages[:-1],
        )
        assistant_message = AssistantMessage.objects.create(
            session=session,
            role=AssistantMessage.Role.ASSISTANT,
            body=assistant_body,
            presentation=build_assistant_presentation(next_state, proposal_payloads),
        )
        actions = [
            AssistantActionProposal.objects.create(**{**proposal_data, "message": assistant_message})
            for proposal_data in proposal_payloads
        ]
        if not session.title or session.title == default_session_title(session.page_type):
            session.title = serializer.validated_data["body"][:24]
        session.state = next_state
        session.save(update_fields=["title", "state", "updated_at"])

        return Response(
            {
                "user_message": AssistantMessageSerializer(user_message).data,
                "assistant_message": AssistantMessageSerializer(assistant_message).data,
                "session": AssistantSessionSerializer(session).data,
                "actions": AssistantActionProposalSerializer(actions, many=True).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AssistantSessionActionListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AssistantActionProposalSerializer

    def get_queryset(self):
        session = get_object_or_404(AssistantSession, pk=self.kwargs["session_id"], user=self.request.user)
        return AssistantActionProposal.objects.filter(
            session=session,
            user=self.request.user,
            status=AssistantActionProposal.Status.PENDING,
            expires_at__gt=timezone.now(),
        ).order_by("-created_at")


class AssistantActionExecuteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, action_id):
        proposal = get_object_or_404(
            AssistantActionProposal.objects.select_related("user", "session", "message"),
            pk=action_id,
            user=request.user,
        )
        result = execute_action(proposal)
        proposal.status = AssistantActionProposal.Status.EXECUTED
        proposal.executed_at = timezone.now()
        proposal.result = result
        proposal.save(update_fields=["status", "executed_at", "result", "updated_at"])
        return Response(
            {
                "action": AssistantActionProposalSerializer(proposal).data,
                "result": result,
            },
            status=status.HTTP_200_OK,
        )


class AssistantActionDismissAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, action_id):
        proposal = get_object_or_404(
            AssistantActionProposal,
            pk=action_id,
            user=request.user,
            status=AssistantActionProposal.Status.PENDING,
        )
        proposal.status = AssistantActionProposal.Status.DISMISSED
        proposal.save(update_fields=["status", "updated_at"])
        return Response({"action": AssistantActionProposalSerializer(proposal).data}, status=status.HTTP_200_OK)
