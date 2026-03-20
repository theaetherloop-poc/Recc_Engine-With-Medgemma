# Aether AI Engine Crew

Welcome to the Aether AI Engine Crew project, powered by [crewAI](https://crewai.com). 

## Installation

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```
### Customizing

**Add your `MODEL, AZURE_API_KEY, AZURE_API_BASE, AZURE_API_VERSION and SERPER_API_KEY` into the `.env` file**

The code was tested with gpt-4o deployed on azure.


- Modify `src/aether_2/config/agents.yaml` to define your agents
- Modify `src/aether_2/config/tasks.yaml` to define your tasks
- Modify `src/aether_2/crew.py` to add your own logic, tools and specific args
- Modify `src/aether_2/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart the crew of AI agents and begin task execution, run this from the root folder of the project:

```bash
$ crewai run
```

This command initializes the aether-ai-engine Crew, assembling the agents and assigning them tasks as defined in your configuration.


## Understanding Your Crew

The aether-ai-engine Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.


About the tools - 

biomarker_evaluation.py
The biomarker_evaluation tool evaluates a person’s biomarker measurements against a predefined set of reference ranges. It takes a JSON string containing the person’s age, sex assigned at birth, and biomarker values, then looks up the relevant ranges for each biomarker, which may differ by sex or age. Each range is labeled (e.g., “optimal,” “normal,” “borderline,” “high” or similarly scaled) and mapped to a severity score from 0 (ideal) to 4 (critical). For each biomarker, the code determines which category the value falls into by checking it against the lower and upper bounds of each range. If the severity is 2 or higher, the biomarker is flagged. The result includes a detailed breakdown for every biomarker—its value, unit, category, severity, and range used—as well as a separate list of flagged biomarkers. Biomarkers not found in the reference table are returned with "status": "no_data". The main run method handles parsing the input, performing the evaluation, and returning the results as formatted JSON.

fuzzy_dsld_search_tool.py
The fuzzy_dsld_search tool searches the Dietary Supplement Label Database (DSLD) for products containing a given ingredient name using fuzzy string matching. It takes an ingredient name and a desired number of results, converts the ingredient name to lowercase, and expands it with any predefined synonyms so related terms are also searched. For each candidate term, it compares it against ingredient names in the DSLD dataset using a partial ratio match score from the rapidfuzz library, keeping matches above a threshold of 70. Matching results are sorted in descending order of similarity, and duplicates are removed based on their URL. The tool then returns up to the requested number of top matches, with each result including the product name, ingredient, amount per serving, unit, and the product’s URL.

Usage of SerperDevTool :

The agent when searching for ingredients associated with biomarkers, uses SerperDevTool to look them up at sources like pubmed. # Recc_Engine_Phase3

## Performance Analysis

| User | Biomarkers | Other + Safety | Total | MedGemma issues covered | MedGemma % covered | Gemini issues covered | Gemini % covered | Protocol quality score (MedGemma) | Protocol quality score (Gemini) |
|------|------------|----------------|-------|-------------------------|--------------------|-----------------------|------------------|-----------------------------------|--------------------------------|
| geetahj_at_gmail_com | 19 | 11 | 30 | 28 | 93.30% | 26 | 86.70% | 92% | 88% |
| hello_at_drantonikachanel_com | 21 | 10 | 31 | 28 | 90.30% | 26 | 83.90% | 63% | 66% |
| ian_at_sturgeoncreative_com | 21 | 7 | 28 | 25 | 89.30% | 24 | 85.70% | 78% | 74% |
| kevin_yar_at_omics-os_com | 8 | 7 | 15 | 14 | 93.30% | 13 | 86.70% | 90% | 91% |
| psfrench77_at_gmail_com | 16 | 25 | 37 | 33 | 89.20% | 31 | 83.80% | 69% | 62% |
| ruchida83_at_gmail_com | 18 | 24 | 36 | 32 | 88.90% | 30 | 83.30% | 60% | 64% |
| tusharmhatre2424_at_gmail_com | 18 | 11 | 29 | 26 | 89.70% | 25 | 86.20% | 93% | 89% |
| vitality_at_derricksiu_com | 14 | 15 | 28 | 25 | 89.30% | 23 | 82.10% | 72% | 77% |
| vladimir_at_humaninterfaces_co | 20 | 9 | 25 | 23 | 92.00% | 22 | 88.00% | 81% | 70% |
| test_user_1 | 15 | 11 | 26 | 24 | 92.30% | 22 | 84.60% | 76% | 73% |
| test_user_2 | 12 | 11 | 23 | 20 | 87.00% | 19 | 82.60% | 61% | 65% |
| test_user_3 | 20 | 8 | 28 | 26 | 92.90% | 24 | 85.70% | 91% | 88% |
| test_user_4 | 10 | 15 | 25 | 22 | 88.00% | 21 | 84.00% | 68% | 60% |
| test_user_5 | 18 | 7 | 25 | 23 | 92.00% | 21 | 84.00% | 79% | 74% |
| test_user_11 | 14 | 19 | 33 | 30 | 90.90% | 28 | 84.80% | 62% | 67% |
| test_user_12 | 9 | 11 | 20 | 18 | 90.00% | 17 | 85.00% | 93% | 90% |
| test_user_13 | 22 | 11 | 33 | 29 | 87.90% | 28 | 84.80% | 70% | 72% |
| test_user_14 | 16 | 8 | 24 | 22 | 91.70% | 20 | 83.30% | 84% | 78% |
| test_user_15 | 11 | 18 | 29 | 26 | 89.70% | 24 | 82.80% | 60% | 63% |
