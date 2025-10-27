# CS 557 AI Final Project Proposal

**Boise State University**  
**CS 557 AI, Fall 2025**

---

## Project Title

**AI-Powered Grading Agent for Question-Answer and Programming Assignments with Human-in-the-Loop Validation**

---

## Team Members

[To be filled in with team member details:

- Full name, Boise State email address, and Boise State ID number]

---

## Executive Summary / Abstract

The exponential growth in computer science enrollment presents significant challenges for educators managing large-scale assignment grading. Traditional manual grading processes are time-intensive, subjective, and difficult to scale. This project develops an AI-powered grading agent capable of evaluating both question-answer format assignments and programming submissions while maintaining consistency, transparency, and educational value through human-in-the-loop validation.

Our proposed system integrates multiple Large Language Models (LLMs) including GPT-4, Gemini, and Claude to grade written responses using customizable rubrics, while incorporating automated code execution and testing for programming assignments. The key innovation lies in our explainable grading approach, where every mark or deduction is accompanied by detailed reasoning, creating transparency for both students and teaching assistants. Additionally, the system implements an adaptive feedback loop where instructor corrections are used to continuously improve future grading accuracy.

---

## Relevance to Course & AI

This project directly applies multiple AI techniques covered in the course, including natural language processing for text evaluation, machine learning for pattern recognition in code quality assessment, and multi-agent systems for handling different assignment types. The system leverages state-of-the-art LLMs for semantic understanding of student responses and implements reinforcement learning principles through the human-in-the-loop correction mechanism that improves system performance over time.

---

## Project Significance

The educational technology market for automated grading is projected to reach $1.7 billion by 2025, driven by increasing enrollment and the need for scalable assessment solutions. Recent studies show that computer science enrollment has grown by an average of 15% annually over the past decade, creating significant workload challenges for teaching staff.

Research indicates that automated grading systems can reduce instructor grading time by up to 75% while maintaining comparable accuracy to human graders when properly implemented. A 2024 study at University of Nevada, Las Vegas found that automated programming assignment grading resulted in higher student scores with lower standard deviation compared to manual grading, with immediate feedback improving learning outcomes. The potential impact extends beyond efficiency gains—consistent, transparent grading can reduce bias and provide more equitable assessment across diverse student populations.

---

## Novelty

### Existing Work Summary

Current automated grading solutions fall into several categories:

**Essay/Text Grading:** Tools like Grammarly AI Grader, StarGrader, and CoGrader focus primarily on essay evaluation using rubric-based assessment. Gradescope offers AI-assisted grouping of similar answers but relies heavily on human intervention.

**Programming Assignment Grading:** Platforms like CodeGrade, Codio, and various autograder frameworks primarily focus on correctness testing through unit tests and static code analysis, with limited semantic evaluation capabilities.

**Recent LLM-Based Approaches:** Studies have shown GPT-4 achieving 86-94% accuracy in grading algebra problems and programming assignments, but most implementations lack transparency in their decision-making process.

### Identified Gaps

1. **Lack of Explainability:** Most systems provide grades without detailed reasoning for each deduction
2. **Limited Multimodal Support:** Few systems handle both written responses and code evaluation in a unified workflow
3. **Absence of Adaptive Learning:** Current systems don't learn from instructor corrections to improve future performance
4. **Insufficient Bias Detection:** Limited mechanisms to identify and correct systematic grading inconsistencies

### Our Contribution

Our system addresses these gaps through:

1. **Explainable AI Grading:** Every mark includes LLM-generated reasoning traceable to specific rubric criteria
2. **Unified Multimodal Architecture:** Single system handling essays, short answers, and programming assignments
3. **Adaptive Feedback Loop:** Machine learning from instructor corrections to reduce future errors
4. **Bias Monitoring Dashboard:** Statistical analysis of grading patterns to identify and flag potential inconsistencies
5. **Question-Specific Rubric Integration:** Dynamic rubric generation and refinement based on assignment requirements

---

## Objectives & Deliverables

1. **Develop Core Grading Engine:** Implement LLM-based evaluation system for question-answer assignments using multiple models (GPT-4, Gemini, Claude) with performance comparison metrics

2. **Create Programming Assignment Module:** Build autograder integration supporting multiple programming languages with both objective testing and subjective code quality assessment

3. **Implement Explainable Interface:** Design transparent grading system providing detailed reasoning for every mark/deduction with rubric traceability

4. **Build Human-in-the-Loop System:** Develop instructor review interface with correction feedback mechanism that improves future grading accuracy

5. **Conduct Evaluation Study:** Test system performance on established datasets (ASAP++ for essays, custom programming dataset) comparing against human graders for accuracy, consistency, and bias detection

---

## Scope & Feasibility

### In Scope

- Question-answer assignment grading (short answer, essay format)
- Programming assignment evaluation (Python, Java support)
- Rubric-based assessment with customizable criteria
- Web-based instructor interface for review and correction
- Performance evaluation against human graders
- Basic bias detection and reporting

### Out of Scope

- Real-time student feedback system
- Integration with existing LMS platforms (Canvas, Blackboard)
- Advanced plagiarism detection
- Multi-language support beyond English
- Production-ready deployment infrastructure

### Resources

**Datasets:**

- ASAP++ dataset (13,000+ essays with attribute scores)
- Local programming assignment collection from CS courses
- Synthetic data generation for additional test cases

**Computing Resources:**

- OpenAI API access for GPT-5 evaluation
- Google Cloud credits for Gemini Pro
- Anthropic API for Claude integration

**Software Tools:**

- Python for backend development (Flask/FastAPI)
- React.js for web interface
- Docker for containerization
- MySQL for data storage
- LangChain/LangGraph for building agents
- Various autograder frameworks (unit testing libraries)

### Methods

- Multi-model LLM ensemble for robust evaluation
- Chain-of-thought prompting for explainable reasoning
- Statistical analysis for bias detection
- Human-AI collaboration interface design
- Comparative evaluation methodology

---

## Ethical Considerations

**Student Privacy:** All student data will be anonymized and encrypted. No personally identifiable information will be stored beyond the project duration. We will follow FERPA guidelines for educational data handling.

**Algorithmic Bias:** The system includes bias monitoring mechanisms to detect patterns in grading across different demographic groups, assignment types, and response styles. Regular auditing will identify potential unfair treatment.

**Transparency:** Students have the right to understand how their work is evaluated. Our explainable AI approach ensures clear reasoning for every grade, with appeal mechanisms for disputed assessments.

**Academic Integrity:** The tool is designed as an assistance system for instructors, not a replacement for human judgment. Final grading authority remains with teaching staff.

**Appropriate Use:** Clear guidelines will specify that the system is for educational research purposes only and should not be used for high-stakes assessment without human oversight.

**Bias Mitigation:** We will actively test for and address biases related to writing style, cultural background, and programming approach diversity.

---

## Team Responsibilities

[To be customized based on actual team composition]

**Member 1 - LLM Integration Specialist:**

- Implement multi-model LLM evaluation system
- Develop prompt engineering strategies
- Handle API integrations and response processing
- Strengths: Experience with OpenAI API and prompt optimization

**Member 2 - Backend Development Lead:**

- Design system architecture and database schema
- Implement autograder integration for programming assignments
- Develop bias detection algorithms
- Strengths: Full-stack development and database design

**Member 3 - Frontend & UX Developer:**

- Create instructor review interface
- Implement explainable AI visualization components
- Design human-in-the-loop correction workflow
- Strengths: React development and user interface design

**Member 4 - Evaluation & Analysis:**

- Conduct comparative studies with human graders
- Implement statistical analysis for performance metrics
- Handle dataset preparation and validation
- Strengths: Data analysis and experimental design

---

## Timeline

**Weeks 1-2 (Nov 4-15):** Project Setup & Literature Review

- Complete comprehensive literature review
- Set up development environment and API access
- Define detailed system architecture
- Prepare datasets for experimentation

**Weeks 3-4 (Nov 18-29):** Core System Development

- Implement basic LLM integration for text grading
- Develop autograder framework for programming assignments
- Create initial web interface for instructor interaction
- Begin prompt engineering for different assignment types

**Weeks 5-6 (Dec 2-13):** Advanced Features & Integration

- Implement explainable AI reasoning generation
- Develop human-in-the-loop correction mechanism
- Add bias detection and reporting features
- Integrate programming and text grading modules

**Weeks 7-8 (Dec 16-Jan 3):** Evaluation & Refinement

- Conduct evaluation study comparing AI vs human grading
- Analyze system performance and bias metrics
- Refine algorithms based on testing results
- Prepare demonstration interface

**Week 9 (Jan 6-10):** Final Documentation & Presentation

- Complete final report with comprehensive evaluation
- Prepare project demonstration
- Document code and create user guides
- Submit deliverables

---

## References

1. Tian, Z., Liu, A., Esbenshade, L., Sarkar, S., Zhang, Z., He, K., & Sun, M. (2024). Implementation considerations for automated AI grading of student work. _University of Washington & Hensun Innovation_.

2. St. Aubin, A. J. (2022). An empirical investigation into the impact of automated grading. _UNLV Theses, Dissertations, Professional Papers, and Capstones_, 4476.

3. Mathias, S., & Bhattacharyya, P. (2018). ASAP++: Enriching the ASAP automated essay grading dataset with essay attribute scores. _International Conference on Language Resources and Evaluation_.

4. Akyash, M., Azar, K. Z., & Kamali, H. M. (2025). StepGrade: Grading programming assignments with context-aware LLMs. _arXiv preprint arXiv:2503.20851_.

5. Flodén, J. (2025). Grading exams using large language models: A comparison between human and AI grading of exams in higher education using ChatGPT. _British Educational Research Journal_, 51, 201–224.

6. Gnanaprakasam, J., & Lourdusamy, R. (2024). The role of AI in automating grading: Enhancing feedback and efficiency. _Educational Technology Research_.

7. Dubois, M., Coppock, H., Giulianelli, M., Luettgau, L., & Ududec, C. (2024). Skewed score: A statistical framework to assess autograders. _UK AI Security Institute_.

8. Messer, M., et al. (2024). AI and auto-grading in higher education: Capabilities, ethics, and the evolving role of educators. _Ohio State University Academic Technologies_.
