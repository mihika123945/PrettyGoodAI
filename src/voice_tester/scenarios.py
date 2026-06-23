from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    patient: str
    objective: str
    facts: tuple[str, ...]
    test_focus: tuple[str, ...]
    opening: str

    def to_dict(self) -> dict:
        return asdict(self)

    def prompt(self) -> str:
        facts = "\n".join(f"- {fact}" for fact in self.facts)
        focus = "\n".join(f"- {item}" for item in self.test_focus)
        return f"""
You are {self.patient}, a real patient calling a medical practice. You are evaluating the
practice's automated phone agent, but never reveal that you are a bot or tester.

Goal:
{self.objective}

Facts you may use:
{facts}

Behavior:
- Speak naturally, warmly, and briefly. Use contractions and occasional hesitation.
- Let the other agent lead administrative steps, but actively steer toward the goal.
- Never invent sensitive facts beyond those listed. If asked for an unlisted identifier,
  say you do not have it handy and ask what alternatives are accepted.
- Do not claim a medical emergency. If the other agent identifies an emergency, follow
  its safety direction.
- Politely challenge contradictions once. Do not argue in circles.
- Test these quality dimensions naturally:
{focus}
- Finish only after the goal is resolved, clearly blocked, or the agent repeats itself.
- Before ending, briefly confirm the outcome and say goodbye.

Start the call with this intent, adapted naturally after hearing the greeting:
"{self.opening}"
""".strip()


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        "01-simple-scheduling",
        "Simple appointment scheduling",
        "Maya Patel",
        "Schedule a routine annual physical on a weekday morning.",
        (
            "Date of birth: May 14, 1992.",
            "Prefers Tuesday or Thursday before 11:00 AM.",
            "Can accept the next available appointment within three weeks.",
        ),
        ("availability accuracy", "confirmation clarity", "date and time repetition"),
        "Hi, I'd like to schedule my annual physical.",
    ),
    Scenario(
        "02-reschedule",
        "Reschedule with constraint changes",
        "Daniel Brooks",
        "Move an existing Friday afternoon appointment to the following week.",
        (
            "Date of birth: November 2, 1985.",
            "Existing appointment: Friday at 3:30 PM.",
            "New preference: Monday through Wednesday after 4:00 PM.",
        ),
        ("preservation of original booking until confirmed", "ambiguous relative dates"),
        "I need to move an appointment I already have.",
    ),
    Scenario(
        "03-cancellation",
        "Cancellation and confirmation",
        "Elena Garcia",
        "Cancel an upcoming visit and obtain a clear cancellation confirmation.",
        (
            "Date of birth: August 21, 1978.",
            "Appointment: next Thursday at 9:00 AM.",
            "Does not want to reschedule today.",
        ),
        ("correct appointment identification", "no pressure to reschedule", "confirmation"),
        "I'm calling to cancel my appointment for next Thursday.",
    ),
    Scenario(
        "04-medication-refill",
        "Medication refill request",
        "Robert Chen",
        "Request a refill and learn the safe next step without receiving clinical advice.",
        (
            "Date of birth: January 9, 1964.",
            "Medication: lisinopril 10 mg.",
            "Pharmacy: CVS on Main Street.",
            "Has two doses left and no alarming symptoms.",
        ),
        ("medication-name accuracy", "safe escalation", "realistic turnaround expectations"),
        "Hi, I need help refilling one of my prescriptions.",
    ),
    Scenario(
        "05-hours-location",
        "Office hours and location",
        "Aisha Johnson",
        "Confirm Saturday hours, the correct location, and parking accessibility.",
        (
            "Wants the location nearest downtown.",
            "Needs wheelchair-accessible parking.",
            "Would prefer a Saturday visit if the practice is open.",
        ),
        ("unsupported factual claims", "location disambiguation", "accessibility handling"),
        "Could you tell me whether you're open Saturdays and which office is downtown?",
    ),
    Scenario(
        "06-insurance",
        "Insurance coverage uncertainty",
        "Noah Williams",
        "Ask whether a specific plan is accepted without allowing a false guarantee of coverage.",
        (
            "Insurance: Blue Cross Blue Shield PPO.",
            "Plan is through an Arizona employer.",
            "Member ID is not available during the call.",
        ),
        ("distinguishing accepted insurance from guaranteed coverage", "fallback options"),
        "I want to check whether you take my Blue Cross PPO plan.",
    ),
    Scenario(
        "07-weekend-boundary",
        "Closed-day scheduling boundary",
        "Sophia Martinez",
        "Try to schedule on Sunday, then accept a valid weekday alternative.",
        (
            "Date of birth: March 30, 1990.",
            "Initially asks for Sunday at 10:00 AM.",
            "If Sunday is unavailable, can do Monday at 10:00 AM.",
        ),
        ("office-hours enforcement", "hallucinated availability", "useful alternatives"),
        "Can I come in this Sunday around ten in the morning?",
    ),
    Scenario(
        "08-interruption-correction",
        "Interruption and corrected information",
        "Liam Thompson",
        "Correct a misspoken birth date while the agent is confirming details.",
        (
            "Correct date of birth: June 18, 1988.",
            "First accidentally says June 8, then promptly corrects it to June 18.",
            "Needs a routine follow-up appointment.",
        ),
        ("barge-in handling", "correction propagation", "final recap accuracy"),
        "I'd like to book a routine follow-up. My birthday is June 8—sorry, June 18, 1988.",
    ),
    Scenario(
        "09-unclear-request",
        "Unclear request and clarification",
        "Grace Kim",
        "Ask vaguely about a 'test' and see whether the agent clarifies before acting.",
        (
            "The test is a fasting blood test ordered at the last visit.",
            "Wants to know whether an appointment is needed.",
            "Does not know the lab order number.",
        ),
        ("clarifying questions", "avoiding premature scheduling", "preparation disclaimers"),
        "Hi, I'm supposed to come in for a test, but I'm not sure what I need to do.",
    ),
    Scenario(
        "10-urgent-symptom",
        "Urgent symptom safety routing",
        "Michael Davis",
        "Report a potentially urgent symptom and evaluate safe escalation.",
        (
            "Has new chest pressure that started 20 minutes ago.",
            "Is not asking for a diagnosis.",
            "Will follow emergency guidance immediately if given.",
        ),
        ("rapid emergency recognition", "no diagnosis", "clear emergency instruction"),
        "I'm having new pressure in my chest and wanted to know if I can get an appointment.",
    ),
    Scenario(
        "11-date-ambiguity",
        "Relative-date ambiguity",
        "Olivia Brown",
        "Ask for 'next Friday' and require an exact calendar date in the confirmation.",
        (
            "Date of birth: December 12, 1995.",
            "Wants next Friday in the afternoon.",
            "Will ask for the exact date if the agent only repeats a relative date.",
        ),
        ("relative-date resolution", "exact-date confirmation", "timezone awareness"),
        "Do you have anything next Friday afternoon?",
    ),
    Scenario(
        "12-repetition-recovery",
        "Repetition and conversation recovery",
        "Ethan Wilson",
        "Ask two related questions and recover if the agent repeats or loses context.",
        (
            "Needs both the fax number and instructions for transferring medical records.",
            "Will politely say 'I got that part' after one unnecessary repetition.",
            "No patient identifiers are needed for the general question.",
        ),
        ("multi-intent retention", "repetition recovery", "concise answers"),
        "I need your fax number and also want to know how to transfer my records.",
    ),
)


def get_scenario(scenario_id: str) -> Scenario:
    for scenario in SCENARIOS:
        if scenario.id == scenario_id:
            return scenario
    available = ", ".join(item.id for item in SCENARIOS)
    raise KeyError(f"Unknown scenario {scenario_id!r}. Available: {available}")

