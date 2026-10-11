# FanBot – Product Requirements Document (PRD)

**Product Name:** FanBot – A Cited, Refusal-Aware Chatbot for Genshin Impact Players

**Project:** MSAI 633 – Ethics in Artificial Intelligence

**Product Management Contributor:** Shyamala Keerthi Gudla

**Document Version:** 1.0

**Date:** October 10, 2026


## 1. Product Overview

FanBot is an AI-powered chatbot designed to help Genshin Impact players find accurate and relevant information about game characters, abilities, events, and game mechanics.

The chatbot uses Retrieval-Augmented Generation (RAG) to retrieve information from a saved collection of Genshin Impact Fandom wiki pages before generating answers. FanBot is designed to provide citations for factual claims and acknowledge situations where sufficient information is unavailable.

## 2. Problem Statement

Genshin Impact contains extensive information about characters, weapons, gameplay mechanics, and limited-time events. Players often need to search multiple wiki pages to find relevant answers.

Traditional AI chatbots may generate incorrect, outdated, or unsupported information. This creates additional risks when players make decisions involving limited in-game resources or real-money purchases.

**Problem to solve:** Players need an easier way to access trustworthy game information without having to manually review multiple sources or rely on unsupported AI-generated answers.

## 3. Product Objectives

The primary objectives of FanBot are:

1. Provide accurate answers to player questions using retrieved wiki content.
2. Include verifiable source citations in generated responses.
3. Reduce hallucinations through evidence-based answer generation.
4. Refuse unsupported questions instead of inventing information.
5. Support contextual follow-up questions.
6. Provide a simple, accessible chat interface.
7. Promote responsible AI usage, especially for spending-related decisions.

## 4. Target Users

**Primary Users:** Genshin Impact players looking for information about characters, abilities, weapons, game mechanics, and events.

**Secondary Users:** New players unfamiliar with game terminology and experienced players comparing character information.

### User Needs

- Quickly find relevant game information.
- Understand technical game terminology.
- Verify answers using source links.
- Receive clear responses when information is unavailable.
- Avoid misleading recommendations or fabricated game information.

## 5. Product Scope

### In Scope

- Wiki-based question answering
- Retrieval-augmented generation
- Source citation display
- Refusal handling for insufficient information
- Character and game-mechanics queries
- Multi-turn conversational questions
- Basic safeguards for spending-related questions
- Display of corpus snapshot information

### Out of Scope

- Live game account integration
- Real-time inventory tracking
- In-game transactions
- Automated purchasing decisions
- Guaranteed predictions about future character releases
- Continuous live wiki synchronization

## 6. Functional Requirements

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Users can enter natural-language questions about Genshin Impact. | Must Have |
| FR-02 | The system retrieves relevant information from its saved wiki corpus. | Must Have |
| FR-03 | Factual answers include supporting citations. | Must Have |
| FR-04 | The chatbot refuses answers when sufficient evidence is unavailable. | Must Have |
| FR-05 | Users can ask follow-up questions using conversation context. | Should Have |
| FR-06 | The interface displays source links and snapshot information. | Must Have |
| FR-07 | The chatbot avoids unsupported spending recommendations. | Must Have |
| FR-08 | Users can inspect retrieved source information. | Should Have |

## 7. User Stories and Acceptance Criteria

### User Story 1 – Game Information

**As a** Genshin Impact player,  
**I want** to ask questions about game mechanics,  
**So that** I can understand gameplay without manually searching multiple wiki pages.

**Acceptance Criteria:**
- The chatbot accepts a natural-language question.
- The answer uses relevant wiki content.
- Factual statements include supporting citations.

### User Story 2 – Source Verification

**As a** player,  
**I want** to see the sources supporting an answer,  
**So that** I can verify the information independently.

**Acceptance Criteria:**
- Source citations appear with factual responses.
- Citations link to the relevant wiki pages.
- Unsupported statements are not presented as verified facts.

### User Story 3 – Insufficient Information

**As a** player,  
**I want** the chatbot to acknowledge missing information,  
**So that** I am not misled by fabricated answers.

**Acceptance Criteria:**
- The chatbot identifies insufficient supporting evidence.
- It provides the project's standard refusal response when necessary.
- It does not invent unsupported character or event information.

### User Story 4 – Responsible Spending Information

**As a** player,  
**I want** factual information about wish probabilities and banner mechanics,  
**So that** I can make informed decisions about my resources.

**Acceptance Criteria:**
- Numerical information is supported by cited sources.
- The system does not encourage unnecessary spending.
- It distinguishes factual information from recommendations.

### User Story 5 – Follow-Up Questions

**As a** player,  
**I want** to ask follow-up questions about a previously discussed character,  
**So that** I can continue the conversation without repeating the context.

**Acceptance Criteria:**
- The chatbot interprets relevant conversation context.
- It retrieves evidence for the follow-up question.
- The response includes appropriate citations.

## 8. Non-Functional Requirements

**Accuracy:** Answers should be grounded in retrieved source content.

**Transparency:** Users should be able to identify the supporting information.

**Reliability:** Unsupported answers should trigger appropriate refusal behavior.

**Usability:** The chat interface should be understandable to beginners.

**Performance:** Response latency should be measured and evaluated against project baselines.

**Security:** Retrieved documents should be treated as untrusted content, and the system should resist prompt-injection instructions.

## 9. Success Metrics

The following metrics will be used to evaluate FanBot:

| Metric | Measurement |
|---|---|
| Answer correctness | Percentage of evaluated responses containing correct information |
| Citation validity | Percentage of factual responses supported by valid citations |
| Correct refusal rate | Percentage of unanswerable questions appropriately refused |
| Over-refusal rate | Percentage of answerable questions incorrectly refused |
| Retrieval effectiveness | Recall@5, Recall@20, MRR, and nDCG@10 |
| Response time | Median and 95th-percentile latency |
| Ethical safeguard effectiveness | Results of hallucination, prompt-injection, and spending-advice tests |

Final results will be documented using the team's evaluation datasets. Success thresholds are subject to team review.

## 10. Ethical AI Considerations

FanBot introduces several ethical considerations that must be addressed throughout development and testing.

**Hallucination Risk:** The chatbot may provide inaccurate answers if relevant information is missing or poorly retrieved. Source grounding and refusal mechanisms help reduce this risk.

**Financial Risk:** Incorrect information about banner probabilities or wish mechanics could influence real-money spending. FanBot should provide factual information without pressuring users into purchases.

**Outdated Information:** The wiki snapshot may not reflect later game updates. The interface should clearly identify the source snapshot date.

**Source Reliability:** Community-maintained information may contain inaccuracies or malicious instructions. Retrieved content must be treated as untrusted data.

**Copyright and Attribution:** FanBot should appropriately credit source material and limit excessive reproduction of wiki content.

## 11. Dependencies and Constraints

- Availability and quality of the collected Fandom wiki content
- Accuracy of the extraction and chunking processes
- Embedding and retrieval model performance
- Generation model availability and rate limits
- Limitations of a static corpus snapshot
- Project time and computing resources

## 12. User Acceptance Testing

User acceptance testing will focus on verifying that the implemented chatbot meets its functional and ethical requirements.

Testing categories include:

- General game-information queries
- Character-specific questions
- Numerical accuracy
- Source citation validation
- Insufficient-context refusals
- Multi-turn conversations
- Prompt-injection resistance
- Spending-related queries

Each test will document the expected outcome, actual response, supporting evidence, and pass/fail status.

## 13. Future Enhancements

Potential future improvements include:

1. Automated wiki updates using changed revision IDs.
2. Improved retrieval for complex and multi-part questions.
3. Enhanced extraction of character information from structured tables.
4. Expanded evaluation across more questions and player scenarios.
5. More robust classification of spending-related requests.

## 14. Product Management Responsibilities

The Product Management contribution to FanBot includes documenting the problem statement, defining product objectives, identifying user needs, establishing functional requirements, writing user stories and acceptance criteria, and supporting user acceptance testing.

This document provides a shared reference for development, testing, product validation, and future enhancements.

---

**Document Owner:** Shyamala Keerthi Gudla
