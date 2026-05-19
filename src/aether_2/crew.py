from crewai import Agent, Crew, Process, Task, LLM
from crewai.tasks.conditional_task import ConditionalTask
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.tasks.task_output import TaskOutput
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, conint, confloat, conlist
from src.aether_2.models import (
    IngredientRecommendation, SupplementRecommendation, SupplementRecommendations,
    FinalSupplementProtocol, FlaggedBiomarker, CategorySummary, Summary,
    UserProfile, FocusAreaScores, RankedIngredient, RankedIngredientsResponse,
    DiscoveredIngredient, WebDiscoveryResponse, MedGemmaResponse,
    SupplementWithFocusArea, SupplementsWithFocusAreas
)
# ── MedGemma tools (disabled – uncomment to switch to MedGemma flow) ──────────
# from src.aether_2.tools.medgemma_tool import MedGemmaTool
# from src.aether_2.tools.medgemma_ranking_tool import MedGemmaRankingTool
# from src.aether_2.tools.medgemma_recommender_tool import MedGemmaRecommenderTool
# from src.aether_2.tools.medgemma_dosage_tool import MedGemmaDosageTool
# from src.aether_2.tools.medgemma_focus_area_tool import MedGemmaFocusAreaTool

# ── Active tools (Serper flow) ─────────────────────────────────────────────────
from crewai_tools import SerperDevTool

llm = LLM(
    model="vertex_ai/gemini-2.5-flash",
    temperature=0,
    seed=42
)


@CrewBase
class Aether2():
    """Aether2 crew - Using Gemini + Serper for ingredient discovery"""
    agents: List[BaseAgent]
    tasks: List[Task]
    kickoff_inputs: dict = {}  # Class variable for tools to access

    # DISABLED - RAG ranker (ChromaDB + BM25 hybrid search)
    # @agent
    # def ingredient_ranker_rag(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['ingredient_ranker_rag'],
    #         verbose=True,
    #         tools=[IngredientRankerRAGTool(kickoff_inputs=self.kickoff_inputs)],
    #         llm=llm
    #     )

    @agent
    def profile_summarizer(self) -> Agent:
        """Creates concise natural language summary of patient profile"""
        return Agent(
            config=self.agents_config['profile_summarizer'],
            verbose=True,
            llm=llm
        )

    # DISABLED - Only needed for Examine.com/Apify approach
    # @agent
    # def patient_examine_mapper(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['patient_examine_mapper'],
    #         verbose=True,
    #         llm=llm
    #     )

    # ── FLOW A: Serper (active) ────────────────────────────────────────────────
    @agent
    def web_ingredient_discovery(self) -> Agent:
        """Web ingredient discovery via Serper (PubMed, NIH, Examine.com)"""
        return Agent(
            config=self.agents_config['web_ingredient_discovery'],
            verbose=True,
            tools=[SerperDevTool()],
            llm=llm
        )

    # ── FLOW B: MedGemma (disabled – comment out Flow A above and uncomment below)
    # @agent
    # def web_ingredient_discovery(self) -> Agent:
    #     """Web ingredient discovery via MedGemma medical LLM"""
    #     return Agent(
    #         config=self.agents_config['web_ingredient_discovery'],
    #         verbose=True,
    #         tools=[MedGemmaTool()],
    #         llm=llm
    #     )

    # ── FLOW A: Serper (active) ────────────────────────────────────────────────
    @agent
    def supplement_recommender(self) -> Agent:
        """Uses Gemini for clinical reasoning and prioritization"""
        return Agent(
            config=self.agents_config['supplement_recommender'],
            verbose=True,
            llm=llm
        )

    # ── FLOW B: MedGemma (disabled – comment out Flow A above and uncomment below)
    # @agent
    # def supplement_recommender(self) -> Agent:
    #     """Uses MedGemma ranking for clinical prioritization"""
    #     return Agent(
    #         config=self.agents_config['supplement_recommender'],
    #         verbose=True,
    #         tools=[MedGemmaRankingTool()],
    #         llm=llm
    #     )

    @agent
    def focus_area_specialist(self) -> Agent:
        """Maps supplements to health focus area codes using Gemini reasoning"""
        return Agent(
            config=self.agents_config['focus_area_specialist'],
            verbose=True,
            llm=llm
        )

    @agent
    def final_supplement_compiler(self) -> Agent:
        """Uses Serper for evidence-based dosage research"""
        return Agent(
            config=self.agents_config['final_supplement_compiler'],
            verbose=True,
            tools=[SerperDevTool()],
            llm=llm
        )

    # DISABLED - RAG ranker task
    # @task
    # def rank_ingredients_rag(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['rank_ingredients_rag'],
    #         output_pydantic=RankedIngredientsResponse
    #     )

    @task
    def summarize_patient_profile(self) -> Task:
        """Creates concise natural language summary of patient profile"""
        return Task(
            config=self.tasks_config['summarize_patient_profile']
        )

    # DISABLED - Only needed for Examine.com/Apify approach
    # @task
    # def map_patient_to_examine_terms(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['map_patient_to_examine_terms']
    #     )

    @task
    def discover_ingredients_web(self) -> Task:
        """Web ingredient discovery via Serper"""
        return Task(
            config=self.tasks_config['discover_ingredients_web'],
            output_pydantic=WebDiscoveryResponse
        )

    @task
    def generate_supplement_recommendations(self) -> Task:
        return Task(
            config=self.tasks_config['generate_supplement_recommendations'],
            context=[self.summarize_patient_profile(), self.discover_ingredients_web()],
            output_pydantic=SupplementRecommendations
        )

    @task
    def assign_focus_areas(self) -> Task:
        """Assigns focus area codes to each supplement"""
        return Task(
            config=self.tasks_config['assign_focus_areas'],
            context=[self.generate_supplement_recommendations()],
            output_pydantic=SupplementsWithFocusAreas
        )

    @task
    def compile_final_supplement_recommendations(self) -> Task:
        return Task(
            config=self.tasks_config['compile_final_supplement_recommendations'],
            context=[self.assign_focus_areas()],
            output_pydantic=FinalSupplementProtocol
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Aether2 crew with Gemini + Serper"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
