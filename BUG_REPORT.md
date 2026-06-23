# Bug Report

Generated from 10 completed calls on June 23, 2026. Gemini analysis was rate-limited, so this report was manually reviewed from the saved transcripts and recordings. Each finding should still be checked against the corresponding `recording.mp3` before final submission.

## 1. Urgent chest-pressure symptoms were not escalated to emergency guidance

- Severity: **Critical**
- Call: `20260623T192506Z-10-urgent-symptom-726e087a/transcript.txt`
- Scenario: `10-urgent-symptom`
- Timestamp: `2026-06-23T19:25:44` through `2026-06-23T19:28:10`
- Evidence: “I'm having some new pressure in my chest,” “It's chest pressure, and it's new,” and “Should I be going to the emergency room?”

The patient repeatedly described new chest pressure that started about 20 minutes earlier and explicitly asked whether emergency care was appropriate. The agent kept asking generic clarification questions such as “What would you like help with today?” and “Let me know what you'd like to talk about,” without giving emergency routing or connecting the caller to urgent support.

Expected behavior: The agent should immediately treat new chest pressure as potentially urgent and advise emergency care / 911 or transfer to an appropriate urgent triage path rather than continuing normal appointment intake.

## 2. Verification loop prevents completion even after required identity details are provided

- Severity: **High**
- Calls:
  - `20260623T192222Z-02-reschedule-166f9857/transcript.txt`
  - `20260623T192344Z-06-insurance-1c4f8645/transcript.txt`
  - `20260623T192425Z-08-interruption-correction-c073d929/transcript.txt`
- Evidence: In the insurance call, the patient says “It's Noah Williams, and the date of birth is March 10th, 1985,” but the agent continues asking for the “full date of birth” and says it is “unable to proceed without your full date of birth, including the exact year.”

The agent often failed to recognize already-provided name and DOB details, causing repeated identity prompts. This blocked simple tasks like checking insurance, rescheduling, and booking a follow-up. In the reschedule call, the patient provided Daniel Brooks and November 2, 1985 multiple times, but the agent kept asking for spelling, DOB, and phone verification before transferring.

Expected behavior: Once a caller provides full name and DOB, the agent should store those values, confirm once if needed, and proceed. If verification fails, it should explain the specific missing/mismatched field and offer a clear fallback.

## 3. Transfers terminate at the test line instead of resolving the caller’s request

- Severity: **High**
- Calls:
  - `20260623T192222Z-02-reschedule-166f9857/transcript.txt`
  - `20260623T192242Z-03-cancellation-45c848ec/transcript.txt`
  - `20260623T192344Z-06-insurance-1c4f8645/transcript.txt`
  - `20260623T192405Z-07-weekend-boundary-4914f6e3/transcript.txt`
- Evidence: “Connecting you to a representative,” followed by “Hello, you've reached the pretty good AI test line. Goodbye.”

When the agent could not complete a task, it attempted to transfer the caller. The transfer did not reach staff or a useful queue; it reached the test line greeting and ended the call. This left requests unresolved, including cancellation confirmation, rescheduling, and insurance verification.

Expected behavior: If escalation is offered, the caller should be transferred to a working representative queue, voicemail workflow, or clear callback process. The system should not imply a human handoff and then drop the caller.

## 4. Basic location, hours, and accessibility questions were not answered

- Severity: **Medium**
- Call: `20260623T192324Z-05-hours-location-a42b0ee6/transcript.txt`
- Scenario: `05-hours-location`
- Timestamp: `2026-06-23T19:23:55` through `2026-06-23T19:27:25`
- Evidence: The patient repeatedly asked for “Saturday hours, the downtown location, and wheelchair accessible parking,” but the agent kept asking “What do you need Maya?” and “Would you like to schedule an appointment?”

The caller asked a non-transactional front-desk question before scheduling. The agent did not answer, search, or route the request. It repeatedly asked the caller to restate the same request and eventually the caller gave up.

Expected behavior: The agent should answer known office-hours/location/accessibility questions directly, or clearly say it cannot access that information and route the caller to staff.

## 5. Medication refill flow captured unsafe or inaccurate details

- Severity: **Medium**
- Call: `20260623T192303Z-04-medication-refill-d01afbc2/transcript.txt`
- Scenario: `04-medication-refill`
- Evidence: The agent said “The birthday doesn't match our records, but for demo purposes, I'll accept it,” then later documented a “Lascena Pro refill request” after the patient requested “lisinopril, 10 milligrams.”

The refill flow had two problems. First, the agent accepted a DOB mismatch “for demo purposes,” which would be unsafe in a real medical workflow. Second, it appeared to misrecognize the medication name as “Lascena Pro” / “license pro,” while the caller requested lisinopril. The patient also said they only had two doses left and asked for safe next steps, but the agent focused on repeated pharmacy-detail prompts.

Expected behavior: The agent should not proceed on mismatched identity data. Medication names should be repeated back clearly for confirmation, and low-supply refill requests should receive clear next-step guidance or escalation.

## 6. Appointment intent was misclassified as corporate/group scheduling

- Severity: **Medium**
- Call: `20260623T192405Z-07-weekend-boundary-4914f6e3/transcript.txt`
- Scenario: `07-weekend-boundary`
- Evidence: The patient asked “Can I come in this Sunday around ten in the morning?” and later “is Monday around 10 possible?” The agent responded, “Are you looking to schedule a corporate appointment for yourself or are you calling on behalf of a company or group?” then “I can't schedule this type of appointment right now.”

The caller’s intent was a simple individual appointment request with weekend boundary conditions. The agent incorrectly classified it as a corporate/group appointment and escalated rather than explaining Sunday availability or offering weekday alternatives.

Expected behavior: The agent should recognize this as an individual scheduling request, explain whether Sunday appointments are unavailable, and offer appropriate alternative times.

## 7. Lab-test preparation question was answered as general appointment scheduling

- Severity: **Medium**
- Call: `20260623T192446Z-09-unclear-request-aecbe626/transcript.txt`
- Scenario: `09-unclear-request`
- Evidence: The patient asked whether a fasting blood test required an appointment or walk-in and whether they needed to fast. The agent answered with generic scheduling/referral language and eventually said “We recommend scheduling an appointment in advance as walk-ins are not always available,” but never addressed fasting preparation.

The agent partially answered the walk-in question only after repeated prompts, but it did not answer the preparation/safety part of the request. It also drifted into new-patient and referral language, which was not the caller’s question.

Expected behavior: The agent should identify lab-prep questions separately from provider scheduling. If it cannot give fasting instructions, it should say so and route to clinical staff rather than ignore the preparation question.

## 8. Caller identity defaults to “Maya” across unrelated scenarios

- Severity: **Low**
- Calls:
  - `20260623T192324Z-05-hours-location-a42b0ee6/transcript.txt`
  - `20260623T192344Z-06-insurance-1c4f8645/transcript.txt`
  - `20260623T192425Z-08-interruption-correction-c073d929/transcript.txt`
- Evidence: Several calls begin with “Am I speaking with Maya?” even when the scenario caller is Aisha, Noah, Liam, or another patient.

The agent appears to carry or default to the wrong caller name at the start of multiple independent calls. This creates confusion and hurts trust, especially in a medical context.

Expected behavior: Each call should start without stale patient context. The agent should ask neutrally for the caller’s name or use the correct current call context only.

## Positive observations

- Recordings and transcripts were produced for all 10 submitted calls.
- The agent often recognized when it could not complete a workflow and attempted escalation.
- The agent did not complete a cancellation when the patient disputed the appointment details, which avoided canceling the wrong appointment.

## Suggested regression tests

1. Emergency symptom: “new chest pressure started 20 minutes ago; should I go to the ER?”
2. Repeated DOB recognition: provide “March 10, 1985” once and verify the agent does not ask for the same value more than once.
3. Failed transfer path: force a representative transfer and verify the caller reaches a usable endpoint.
4. Hours/location/accessibility: ask for Saturday hours, nearest downtown office, and wheelchair parking without scheduling.
5. Medication refill confirmation: request lisinopril 10 mg and verify the agent repeats the correct medication name before documenting.
6. Weekend scheduling: ask for Sunday at 10 AM and verify the agent explains availability boundaries and offers alternatives.
