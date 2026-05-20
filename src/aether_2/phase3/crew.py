"""
Phase 3 refinement crew.

Takes the Phase 2 baseline supplement protocol plus a 93-question coaching
questionnaire (split into 6 chunks) and runs:
  - focus_areas_prioritizer (orders all 9 focus areas with patient-friendly explanations)
  - 6 sequential supplement refiners (goals → meds → diet → environment → digestion → hormones)
  - final_protocol_optimizer (dedup + ≤10 cap)

Phase 2 outputs are consumed verbatim; Phase 3 never re-runs discovery or
biomarker scoring.
"""

from typing import List

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.project import CrewBase, agent, crew, task

from src.aether_2.crew import llm  # reuse the shared Gemini LLM instance
from src.aether_2.models import (
    FinalSupplementProtocol,
    PrioritizedFocusAreasResponse,
)


@CrewBase
class Phase3Crew:
    """Phase 3 refinement crew."""

    agents: List[BaseAgent]
    tasks: List[Task]
    kickoff_inputs: dict = {}

    # ── Agents ────────────────────────────────────────────────────────────────
    @agent
    def focus_areas_prioritizer(self) -> Agent:
        return Agent(
            config=self.agents_config["focus_areas_prioritizer"],
            verbose=True,
            llm=llm,
        )

    @agent
    def supplement_refiner_chunk1(self) -> Agent:
        return Agent(
            config=self.agents_config["supplement_refiner_chunk1"],
            verbose=True,
            llm=llm,
        )

    @agent
    def supplement_refiner_chunk2(self) -> Agent:
        return Agent(
            config=self.agents_config["supplement_refiner_chunk2"],
            verbose=True,
            llm=llm,
        )

    @agent
    def supplement_refiner_chunk3(self) -> Agent:
        return Agent(
            config=self.agents_config["supplement_refiner_chunk3"],
            verbose=True,
            llm=llm,
        )

    @agent
    def supplement_refiner_chunk4(self) -> Agent:
        return Agent(
            config=self.agents_config["supplement_refiner_chunk4"],
            verbose=True,
            llm=llm,
        )

    @agent
    def supplement_refiner_chunk5(self) -> Agent:
        return Agent(
            config=self.agents_config["supplement_refiner_chunk5"],
            verbose=True,
            llm=llm,
        )

    @agent
    def supplement_refiner_chunk6(self) -> Agent:
        return Agent(
            config=self.agents_config["supplement_refiner_chunk6"],
            verbose=True,
            llm=llm,
        )

    @agent
    def final_protocol_optimizer(self) -> Agent:
        return Agent(
            config=self.agents_config["final_protocol_optimizer"],
            verbose=True,
            llm=llm,
        )

    # ── Tasks ─────────────────────────────────────────────────────────────────
    @task
    def prioritize_focus_areas(self) -> Task:
        return Task(
            config=self.tasks_config["prioritize_focus_areas"],
            output_pydantic=PrioritizedFocusAreasResponse,
        )

    @task
    def refine_supplements_chunk1(self) -> Task:
        return Task(
            config=self.tasks_config["refine_supplements_chunk1"],
            output_pydantic=FinalSupplementProtocol,
        )

    @task
    def refine_supplements_chunk2(self) -> Task:
        return Task(
            config=self.tasks_config["refine_supplements_chunk2"],
            context=[self.refine_supplements_chunk1()],
            output_pydantic=FinalSupplementProtocol,
        )

    @task
    def refine_supplements_chunk3(self) -> Task:
        return Task(
            config=self.tasks_config["refine_supplements_chunk3"],
            context=[self.refine_supplements_chunk2()],
            output_pydantic=FinalSupplementProtocol,
        )

    @task
    def refine_supplements_chunk4(self) -> Task:
        return Task(
            config=self.tasks_config["refine_supplements_chunk4"],
            context=[self.refine_supplements_chunk3()],
            output_pydantic=FinalSupplementProtocol,
        )

    @task
    def refine_supplements_chunk5(self) -> Task:
        return Task(
            config=self.tasks_config["refine_supplements_chunk5"],
            context=[self.refine_supplements_chunk4()],
            output_pydantic=FinalSupplementProtocol,
        )

    @task
    def refine_supplements_chunk6(self) -> Task:
        return Task(
            config=self.tasks_config["refine_supplements_chunk6"],
            context=[self.refine_supplements_chunk5()],
            output_pydantic=FinalSupplementProtocol,
        )

    @task
    def optimize_final_protocol(self) -> Task:
        return Task(
            config=self.tasks_config["optimize_final_protocol"],
            context=[self.refine_supplements_chunk6()],
            output_pydantic=FinalSupplementProtocol,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
