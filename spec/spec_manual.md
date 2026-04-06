# Requirement ID: FR1

- Description: [The system shall clearly label whether each session, course, or feature is free, trial-only, or subscription-required before the user attempts to open it.]
- Source Persona: [Cost-Conscious Seeker]
- Traceability: [Derived from review group G1]
- Acceptance Criteria: [Given a user is browsing content When the user views a session, course, or feature card Then the card must display its access status as Free, Trial, or Subscription Required before the user taps it.]

# Requirement ID: FR2

- Description: [The system shall display the trial duration, renewal price, renewal date, and cancellation method before a user starts a free trial or paid subscription.]
- Source Persona: [Cost-Conscious Seeker]
- Traceability: [Derived from review group G1]
- Acceptance Criteria: [Given a user is about to start a trial or subscription When the purchase confirmation screen is shown Then the screen must display the trial duration, renewal price, renewal date, and a visible cancellation method before the user can confirm.]

# Requirement ID: FR3

- Description: [The system shall provide a self-service subscription management screen where users can view plan details, renewal status, and cancellation options.]
- Source Persona: [Cost-Conscious Seeker]
- Traceability: [Derived from review group G1]
- Acceptance Criteria: [Given a user has an active or trial subscription When the user opens subscription settings Then the system must display the current plan, billing status, next renewal date, and a cancellation path on the same screen.]

# Requirement ID: FR4

- Description: [The system shall start a selected meditation, sleepcast, or audio session within 5 seconds when the user has a stable internet connection.]
- Source Persona: [Routine-Dependent Listener]
- Traceability: [Derived from review group G2]
- Acceptance Criteria: [Given a user is connected to stable internet and selects an online session When the user taps Play Then audio playback must begin within 5 seconds.]

# Requirement ID: FR5

- Description: [The system shall allow downloaded sessions to play without requiring an active internet connection.]
- Source Persona: [Routine-Dependent Listener]
- Traceability: [Derived from review group G2]
- Acceptance Criteria: [Given a user has previously downloaded a session When the device is placed in airplane mode and the user taps Play Then the downloaded session must start and continue playing without an internet connection.]

# Requirement ID: FR6

- Description: [The system shall preserve the playback position of a session if the app is interrupted by a crash, forced close, or temporary loss of connection.]
- Source Persona: [Routine-Dependent Listener]
- Traceability: [Derived from review group G2]
- Acceptance Criteria: [Given a session is playing When the app closes unexpectedly or playback is interrupted Then the system must save the last playback position and offer a Resume option when the user returns to the session.]

# Requirement ID: FR7

- Description: [The system shall provide account recovery options that let users sign in with the correct account method, including email-based login recovery and switching between sign-in methods.]
- Source Persona: [Locked-Out Subscriber]
- Traceability: [Derived from review group G3]
- Acceptance Criteria: [Given a user reaches the sign-in screen When the user selects account help Then the system must provide options to reset a password, recover an email-based account, and switch to a different sign-in method.]

# Requirement ID: FR8

- Description: [The system shall prevent repetitive login loops by showing a specific error message and a corrective action when authentication fails.]
- Source Persona: [Locked-Out Subscriber]
- Traceability: [Derived from review group G3]
- Acceptance Criteria: [Given a user attempts to sign in and authentication cannot be completed When the same sign-in attempt fails twice Then the system must display a specific error message, explain the likely cause, and present at least one corrective action or support option.]

# Requirement ID: FR9

- Description: [The system shall restore access to subscription content immediately after a successful login when the user has an active subscription on the account.]
- Source Persona: [Locked-Out Subscriber]
- Traceability: [Derived from review group G3]
- Acceptance Criteria: [Given a user signs in successfully to an account with an active subscription When the home screen loads Then subscription-only content must be accessible without requiring the user to repurchase or restart the subscription.]

# Requirement ID: FR10

- Description: [The system shall allow users to reach Daily Meditation, Sleep, and Favorites from the home screen in no more than 2 taps.]
- Source Persona: [Overwhelmed Explorer]
- Traceability: [Derived from review group G4]
- Acceptance Criteria: [Given a signed-in user is on the home screen When the user navigates to Daily Meditation, Sleep, or Favorites Then each destination must be reachable in 2 taps or fewer.]

# Requirement ID: FR11

- Description: [The system shall provide search, filtering, and saved-history features that help users find previously used sessions, courses, or sleep content.]
- Source Persona: [Overwhelmed Explorer]
- Traceability: [Derived from review group G4]
- Acceptance Criteria: [Given a user has completed or started content before When the user uses search, filters, or history Then the system must return matching items and allow the user to reopen a previous session or course from the results.]

# Requirement ID: FR12

- Description: [The system shall present a quick-start screen with one-tap access to a breathing exercise, a short meditation, and a sleep option.]
- Source Persona: [Wellbeing-Focused Daily Practitioner]
- Traceability: [Derived from review group G5]
- Acceptance Criteria: [Given a user opens the app and reaches the home screen When the quick-start section is displayed Then the user must be able to start one breathing exercise, one short meditation, and one sleep option with a single tap from that screen.]

# Requirement ID: FR13

- Description: [The system shall allow users to choose a session length before starting a meditation when multiple session lengths are available for the same content.]
- Source Persona: [Wellbeing-Focused Daily Practitioner]
- Traceability: [Derived from review group G5]
- Acceptance Criteria: [Given a meditation offers multiple durations When the user opens the session details Then the system must display the available durations and let the user choose one before playback begins.]

# Requirement ID: FR14

- Description: [The system shall provide a visible progress history showing completed sessions, streaks, or milestones so users can continue long-term mindfulness routines.]
- Source Persona: [Wellbeing-Focused Daily Practitioner]
- Traceability: [Derived from review group G5]
- Acceptance Criteria: [Given a user has completed at least one session When the user opens progress or profile history Then the system must display completed sessions or progress records associated with that account.]