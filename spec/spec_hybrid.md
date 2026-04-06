# Hybrid Specification — Headspace: Meditation & Sleep

**Pipeline:** Hybrid (automated generation refined by manual review)
**Total requirements:** 15

---

# Requirement ID: FR_hybrid_1
- Description: [The system shall display the full subscription price, billing cycle, and renewal date on a dedicated subscription management screen accessible from account settings.]

- Source Persona: [Budget-Conscious Subscriber]
- Traceability: [Derived from review group H1]
- Acceptance Criteria: [Given the user navigates to account settings, When they open the subscription management screen, Then the current plan price, billing cycle, and next renewal date must all be displayed.]
- Notes: [Rewritten from automated requirement to specify exactly what billing information must be shown, replacing vague 'transparent pricing' language.]

---

# Requirement ID: FR_hybrid_2
- Description: [The system shall send an in-app notification at least 7 days before any subscription price change takes effect.]

- Source Persona: [Budget-Conscious Subscriber]
- Traceability: [Derived from review group H1]
- Acceptance Criteria: [Given a subscription price change is scheduled, When the change is 7 or fewer days away, Then the user must receive an in-app notification stating the old price, new price, and effective date.]
- Notes: [New requirement added based on frequent review complaints about surprise price increases.]

---

# Requirement ID: FR_hybrid_3
- Description: [The system shall provide at least 20 complete meditation sessions and 5 sleepcasts accessible without a paid subscription.]

- Source Persona: [Budget-Conscious Subscriber]
- Traceability: [Derived from review group H1]
- Acceptance Criteria: [Given a user without a paid subscription opens the app, When they browse available content, Then at least 20 meditation sessions and 5 sleepcasts must be accessible and playable in full.]
- Notes: [Rewritten to specify exact minimum free content quantities instead of vague 'enough free content'.]

---

# Requirement ID: FR_hybrid_4
- Description: [The system shall complete the launch sequence and display the home screen within 5 seconds of the user opening the app on a device running Android 10 or later.]

- Source Persona: [Stability-Dependent Daily User]
- Traceability: [Derived from review group H2]
- Acceptance Criteria: [Given the user taps the app icon on a device running Android 10 or later, When the app starts, Then the home screen must be fully loaded and interactive within 5 seconds.]
- Notes: [Rewritten to specify a measurable time threshold and platform, replacing 'the app should load quickly'.]

---

# Requirement ID: FR_hybrid_5
- Description: [The system shall not crash or freeze during audio playback of any meditation session or sleepcast.]

- Source Persona: [Stability-Dependent Daily User]
- Traceability: [Derived from review group H2]
- Acceptance Criteria: [Given the user starts playing any meditation session or sleepcast, When the audio plays from start to finish, Then the app must remain responsive and the audio must complete without crashing or freezing.]
- Notes: [Directly addresses the most common complaint in the performance review group.]

---

# Requirement ID: FR_hybrid_6
- Description: [The system shall preserve the user's meditation streak count, downloaded content, and session history after any app update.]

- Source Persona: [Stability-Dependent Daily User]
- Traceability: [Derived from review group H2]
- Acceptance Criteria: [Given the user has an existing meditation streak and downloaded content, When an app update is installed, Then the streak count, all downloaded sessions, and session history must remain intact.]
- Notes: [Added based on multiple reviews reporting lost streaks and data after updates.]

---

# Requirement ID: FR_hybrid_7
- Description: [The system shall continue playing sleepcast or sleep sound audio when the device screen is locked or turned off.]

- Source Persona: [Sleep-Focused Nighttime User]
- Traceability: [Derived from review group H3]
- Acceptance Criteria: [Given the user starts a sleepcast or sleep sound, When the device screen is locked or turns off automatically, Then the audio must continue playing without interruption.]
- Notes: [Directly addresses the most critical sleep-user complaint: audio stopping when the screen locks.]

---

# Requirement ID: FR_hybrid_8
- Description: [The system shall provide a configurable sleep timer with options of 15, 30, 45, 60, and 90 minutes that stops audio playback at the selected time.]

- Source Persona: [Sleep-Focused Nighttime User]
- Traceability: [Derived from review group H3]
- Acceptance Criteria: [Given the user sets a sleep timer to a specific duration, When that duration elapses, Then audio playback must stop automatically within 10 seconds of the configured time.]
- Notes: [Rewritten to specify exact timer options and acceptable tolerance.]

---

# Requirement ID: FR_hybrid_9
- Description: [The system shall allow users to filter meditation sessions by category, duration, and experience level from the content browsing screen.]

- Source Persona: [Mindfulness-Seeking Meditator]
- Traceability: [Derived from review group H4]
- Acceptance Criteria: [Given the user opens the content browsing screen, When they apply filters for category, duration, or experience level, Then only sessions matching all selected filters must be displayed.]
- Notes: [Addresses navigation complaints from long-term meditators who cannot find specific content types.]

---

# Requirement ID: FR_hybrid_10
- Description: [The system shall recommend meditation sessions based on the user's completed session history and stated goals, updated after each completed session.]

- Source Persona: [Mindfulness-Seeking Meditator]
- Traceability: [Derived from review group H4]
- Acceptance Criteria: [Given the user completes a meditation session, When they return to the home screen, Then the recommended sessions list must reflect their updated history and not suggest sessions completed in the past 7 days.]
- Notes: [Rewritten to include specific recommendation logic, replacing vague 'personalized experience'.]

---

# Requirement ID: FR_hybrid_11
- Description: [The system shall add at least 4 new guided meditation sessions and 2 new sleepcasts to the content library each calendar month.]

- Source Persona: [Mindfulness-Seeking Meditator]
- Traceability: [Derived from review group H4]
- Acceptance Criteria: [Given a new calendar month begins, When the user checks the content library, Then at least 4 new meditation sessions and 2 new sleepcasts not previously available must be present.]
- Notes: [Addresses content repetition complaints with specific monthly minimums.]

---

# Requirement ID: FR_hybrid_12
- Description: [The system shall display a data collection summary screen listing all categories of personal data collected, their purposes, and third parties they are shared with, accessible from account settings.]

- Source Persona: [Privacy-Aware Cautious User]
- Traceability: [Derived from review group H5]
- Acceptance Criteria: [Given the user navigates to account settings, When they open the data collection summary screen, Then a list of all collected data categories, their stated purposes, and any third-party recipients must be displayed.]
- Notes: [Rewritten to specify exactly what the privacy summary must contain.]

---

# Requirement ID: FR_hybrid_13
- Description: [The system shall sync the user's account data including meditation history, streaks, and preferences across all devices logged into the same account within 60 seconds of any change.]

- Source Persona: [Privacy-Aware Cautious User]
- Traceability: [Derived from review group H5]
- Acceptance Criteria: [Given the user completes a session on one device, When they open the app on another device logged into the same account, Then the session must appear in their history within 60 seconds.]
- Notes: [Addresses sync complaints with a specific time threshold.]

---

# Requirement ID: FR_hybrid_14
- Description: [The system shall provide an in-app customer support contact form that confirms receipt of the user's message within 24 hours.]

- Source Persona: [Privacy-Aware Cautious User]
- Traceability: [Derived from review group H5]
- Acceptance Criteria: [Given the user submits a support request through the in-app form, When the request is submitted, Then the system must display a confirmation with a reference number and send an acknowledgment within 24 hours.]
- Notes: [Added based on reviews about unresponsive customer support.]

---

# Requirement ID: FR_hybrid_15
- Description: [The system shall allow the user to cancel their subscription and confirm the cancellation with an on-screen message and email, without requiring the user to contact customer support.]

- Source Persona: [Budget-Conscious Subscriber]
- Traceability: [Derived from review group H1]
- Acceptance Criteria: [Given the user initiates subscription cancellation from account settings, When the cancellation is processed, Then the app must display an on-screen confirmation and send a confirmation email within 5 minutes, without requiring the user to contact support.]
- Notes: [Addresses reviews about difficulty cancelling subscriptions.]

---