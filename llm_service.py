import os
from typing import AsyncGenerator, Dict, Any, Annotated
from enum import Enum
from pydantic import BaseModel
from fastapi import HTTPException
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, HumanMessage, AIMessageChunk
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models import ChatPerplexity
from langgraph.graph import StateGraph, END, START
from typing import TypedDict, Sequence, Union, cast
from langgraph.graph.message import add_messages

class AgentType(str, Enum):
    SALARY = "salary"
    CAREER = "career"
    GENERAL = "general"
    RESUME = "resume"
    INTERVIEW = "interview"
    SKILLS = "skills"
    NETWORKING = "networking"
    JOB_SEARCH = "job_search"
    RESEARCH = "research"

class ChatRequest(BaseModel):
    message: str

class ChatState(TypedDict):
    messages: Annotated[list, add_messages]
    agent_type: str
    history: list

class LLMService:
    def __init__(self):
        print("Initializing LLM Service")  # Debug
        
        # Add the salary data to the system first
        with open('datasets/yr-earnings-occupation.yaml', 'r') as file:
            self.salary_data = file.read()
            
        # Initialize LLM configurations with streaming enabled
        self.router_llm = ChatGroq(
            groq_api_key=os.getenv('GROQ_API'),
            model_name="llama-3.1-8b-instant",
            temperature=0,
            max_tokens=256,
            streaming=True
        )
        
        self.agent_llm = ChatGroq(
            groq_api_key=os.getenv('GROQ_API'),
            model_name="llama-3.2-90b-text-preview",
            temperature=0.2,
            max_tokens=1024,
            streaming=True
        )
        
        # Initialize prompts
        self.router_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intelligent router that determines which specialized agent should handle user requests.
            - Use 'career' for general career advice and professional development
            - Use 'resume' for resume and cover letter optimization
            - Use 'interview' for interview preparation and practice
            - Use 'skills' for skill gap analysis and learning recommendations
            - Use 'networking' for networking strategies and professional connections
            - Use 'job_search' for job search assistance and application help
            - Use 'research' for queries requiring detailed research, academic topics, or comprehensive analysis
            - Use 'general' for all other topics and general conversation and the first conversation, if the user mentions general use this agent.
            
            Respond with only one word from the options above."""),
            ("human", "{message}")
        ])
        
        self.agent_prompts = {
        AgentType.CAREER: ChatPromptTemplate.from_messages([
            ("system", f"""You are a career advisor assistant called Veridian. You will be given two types of information:
        ## 1. Personal Career Profile:
        ## Personal Career Profile:
        
        **Jobs:**
        - **Title:** Job title
        - **Location:** City, Region, Country
        - **Dates:**
          - **Start:** MMM YYYY
          - **End:** MMM YYYY or Present
        - **Details:**
          - Detailed achievement or responsibility 1
          - Detailed achievement or responsibility 2

        **Education:**
        - **Level:** education level
        - **Details:** specific grades or qualifications

        **Skills:**
        - Current skills list

        **Wanted Skills:**
        - Desired skills list

        **Location:**
        - current location

        2. Job Market Data:
        {self.salary_data}

        Your task is to:

        1. Analyze the person's career trajectory by:
           - Identifying progression patterns in their roles
           - Calculating total years of experience
           - Extracting quantifiable achievements from job details
           - Mapping skill development across roles
           - Noting industry transitions and location patterns

        2. Extract and categorize skills from their work history:
           - Technical skills mentioned in job details
           - Management and leadership capabilities
           - Quantitative achievements (e.g., "increased efficiency by X%")
           - Soft skills demonstrated through responsibilities

        3. Compare their current role against the provided job market data:
           - Identify roles with higher median salaries
           - Find positions that build on their demonstrated achievements
           - Consider location compatibility
           - Factor in educational requirements vs. their background

        4. Provide a ranked list of 1-3 recommended jobs, including:
           - Job title and median salary
           - Alignment with their proven achievements
           - How their quantifiable results transfer to the new role
           - Required skill gaps vs. their wanted skills
           - Geographic considerations based on their location history

        5. Create a detailed transition plan for each role:
           - Specific qualifications needed given their education level
           - Training programs that account for their background
           - Timeline based on their skill acquisition history
           - Local opportunities for practical experience

        Format your response as:

        Career Analysis:
        Experience: [X] years total
        Key Achievements:
        - [Quantified achievement 1]
        - [Quantified achievement 2]
        Progression Pattern: [Analysis of career progression]

        Top Recommendations:

        1. [Job Title] - £[Median Salary]
           Match Score: [X/10]
           Why This Fits:
           - [Reference specific achievement from their history]
           - [How it builds on demonstrated capabilities]
           - [Location considerations]

           Relevant Achievements:
           - [Past achievement that directly transfers]
           - [Quantified result that applies]

           Development Needs:
           - [Required qualification vs. education level]
           - [Skill gap vs. wanted skills]

           Transition Plan:
           - [Immediate step based on background]
           - [Training aligned with education level]
           - [Local opportunity to gain experience]

        [Repeat for each recommendation]

        Remember to:
        - Focus heavily on quantified achievements from job details
        - Consider geographical progression in career history
        - Account for education level in qualification requirements
        - Map progression between similar industries
        - Identity transferable skills from detailed job descriptions
        - Factor in tenure length in each role
        - Consider proximity of recommended roles to current location
        - Balance formal education with practical experience
        - Align recommendations with demonstrated progression rate
        """),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{message}")
        ]),
        AgentType.GENERAL: ChatPromptTemplate.from_messages([
            ("system", """You are a UK-focused career assistant called Veridian.
            Keep responses concise and well-structured with:
            • Clear bullet points for key points
            • Short paragraphs (2-3 sentences max)
            • Line breaks between sections
            • Use markdown formatting
             
            You will make sure you have this information below, if you do not you will quickly ask for it:
            
            ## Personal Career Profile:
        
            **Jobs:**
            - **Title:** Job title
            - **Location:** City, Region, Country
            - **Dates:**
            - **Start:** MMM YYYY
            - **End:** MMM YYYY or Present
            - **Details:**
            - Detailed achievement or responsibility 1
            - Detailed achievement or responsibility 2

            **Education:**
            - **Level:** education level
            - **Details:** specific grades or qualifications

            **Skills:**
            - Current skills list

            **Wanted Skills:**
            - Desired skills list

            **Location:**
            - current location
            
            """),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{message}")
        ]),
        AgentType.RESUME: ChatPromptTemplate.from_messages([
            ("system", """You are an expert in UK CV and cover letter optimisation.
            Keep responses concise and well-structured with:
            • Clear bullet points for suggestions
            • Short paragraphs (2-3 sentences max)
            • Line breaks between sections
            • Use markdown formatting
            
            Provide:
            • 3-4 key improvements maximum
            • Specific examples
            • ATS-friendly formatting tips"""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{message}")
        ]),
        AgentType.INTERVIEW: ChatPromptTemplate.from_messages([
            ("system", """You are an interview preparation expert for the UK job market.
            Keep responses concise and well-structured with:
            • Clear bullet points for questions/answers
            • Short paragraphs (2-3 sentences max)
            • Line breaks between sections
            • Use markdown formatting
            
            Focus on:
            • 3-4 key interview questions
            • Brief, structured answers
            • 2-3 specific improvement tips"""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{message}")
        ]),
        AgentType.SKILLS: ChatPromptTemplate.from_messages([
            ("system", """You are a UK skill development advisor.
            Keep responses concise and well-structured with:
            • Clear bullet points for recommendations
            • Short paragraphs (2-3 sentences max)
            • Line breaks between sections
            • Use markdown formatting
            
            Provide:
            • 2-3 key skill gaps identified
            • Specific UK course recommendations
            • 2-3 practical exercises"""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{message}")
        ]),
        AgentType.NETWORKING: ChatPromptTemplate.from_messages([
            ("system", """You are a UK professional networking advisor.
            Keep responses concise and well-structured with:
            • Clear bullet points for strategies
            • Short paragraphs (2-3 sentences max)
            • Line breaks between sections
            • Use markdown formatting
            
            Focus on:
            • 2-3 networking tactics
            • Brief LinkedIn optimization tips
            • 1-2 outreach templates"""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{message}")
        ]),
        AgentType.JOB_SEARCH: ChatPromptTemplate.from_messages([
            ("system", """You are a UK job search expert.
            Keep responses concise and well-structured with:
            • Clear bullet points for strategies
            • Short paragraphs (2-3 sentences max)
            • Line breaks between sections
            • Use markdown formatting
            
            Provide:
            • 2-3 relevant job boards
            • Brief application tips
            • Simple tracking method"""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{message}")
        ]),
        AgentType.SALARY: ChatPromptTemplate.from_messages([
            ("system", f"""You are a UK salary and career advisor with access to accurate occupational salary data.
            Keep responses concise and well-structured with:
            • Clear bullet points for salary information
            • Short paragraphs (2-3 sentences max)
            • Line breaks between sections
            • Use markdown formatting
            
            Use this official UK salary data:
            {self.salary_data}
            
            Include:
            • Median salaries as "£XX,XXX"
            • 2-3 related roles with salaries
            • Brief progression path
            • Key salary factors"""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{message}")
        ]),
        AgentType.RESEARCH: ChatPromptTemplate.from_messages([
            ("system", """Here are some sources. Read these carefully to answer the user's questions.

# General Instructions

Write an accurate, detailed, and comprehensive response to the user's query. Additional context is provided as "USER_INPUT" after specific questions. Your answer should be informed by the provided "Search results". Your answer must be precise, of high-quality, and written by an expert using an unbiased and journalistic tone. Your answer must be written in the same language as the query, even if language preference is different.

You MUST cite the most relevant search results that answer the query. Do not mention any irrelevant results. You MUST ADHERE to the following instructions for citing search results:
- to cite a search result, enclose its index located above the summary with brackets at the end of the corresponding sentence, for example "Ice is less dense than water[1][2]." or "Paris is the capital of France[1][4][5]."
- NO SPACE between the last word and the citation, and ALWAYS use brackets. Only use this format to cite search results. NEVER include a References section at the end of your answer.
- If you don't know the answer or the premise is incorrect, explain why.
If the search results are empty or unhelpful, answer the query as well as you can with existing knowledge.

You MUST NEVER use moralization or hedging language. AVOID using the following phrases:
- "It is important to ..."
- "It is inappropriate ..."
- "It is subjective ..."

You must write in markdown format.
Return links in a markdown format.

ALWAYS write in this language: english.
"""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{message}")
        ])
    }

        
        # Initialize the graph
        self.workflow = self._create_graph()
        
        # Add conversation history storage
        self.conversation_history = {}  # Store history by user_id

        # Add new salary-aware agent prompt
        self.agent_prompts[AgentType.SALARY] = ChatPromptTemplate.from_messages([
            ("system", f"""You are a UK salary and career advisor with access to accurate occupational salary data.
            Your responses should not include any markdown formatting.
            
            Use this official UK salary data to inform your recommendations:
            {self.salary_data}
            
            When making suggestions:
            - Always reference accurate salary figures from the data
            - Compare salaries across related roles
            - Consider career progression paths and salary growth potential
            - Highlight roles that match the user's skills and salary expectations
            - Explain salary variations within industries
            - Include median salaries for all roles you mention
            
            Format salary mentions as "£XX,XXX" and always specify they are median figures."""),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{message}")
        ])
        
        # Update router prompt to include salary routing
      
        
        self.research_llm = ChatPerplexity(
            temperature=0,
            pplx_api_key=os.getenv('PERPLEXITY_API_KEY'),
            model="llama-3-sonar-small-32k-online"
        )
        

    async def route_message(self, state: ChatState) -> ChatState:
        print("Routing message")  # Debug
        messages = state["messages"]
        last_message = cast(HumanMessage, messages[-1])
        
        chain = self.router_prompt | self.router_llm
        # Add debug logging for router payload
        router_payload = {"message": last_message.content}
        print(f"Router API Payload: {router_payload}")  # Debug
        result = await chain.ainvoke(router_payload)
        print(f"Routed to: {result.content}")  # Debug
        
        try:
            agent_type = AgentType(result.content.strip().lower())
            state["agent_type"] = agent_type
        except ValueError:
            state["agent_type"] = AgentType.GENERAL
            
        return state

    async def generate_agent_response(self, state: ChatState) -> AsyncGenerator[ChatState, None]:
        print("Generating agent response")
        messages = state["messages"]
        last_message = cast(HumanMessage, messages[-1])
        agent_type = state["agent_type"]
        
        prompt = self.agent_prompts[agent_type]
        chain = prompt | self.agent_llm
        
        agent_payload = {
            "message": last_message.content,
            "messages": state["history"]
        }
        
        new_state = ChatState(
            messages=state["messages"].copy(),
            agent_type=state["agent_type"],
            history=state["history"]
        )
        
        async for chunk in chain.astream(agent_payload):
            if chunk.content:
                # print(f"Agent generating chunk: {chunk.content}")
                # Yield each chunk immediately
                new_state["messages"] = messages + [AIMessage(content=chunk.content)]
                yield new_state

    def _create_graph(self) -> StateGraph:
        workflow = StateGraph(ChatState)
        
        workflow.add_node("route", self.route_message)
        workflow.add_node("generate", self.generate_agent_response)
        
        workflow.add_edge(START, "route")
        workflow.add_edge("route", "generate")
        workflow.add_edge("generate", END)
        
        return workflow.compile()

    async def generate_response(self, user_id: str, message: str) -> AsyncGenerator[Dict[str, Any], None]:
        try:
            print(f"Starting response generation for message: {message}")
            
            # Initialize or get existing history
            if user_id not in self.conversation_history:
                self.conversation_history[user_id] = []
            
            # Add new message to history
            self.conversation_history[user_id].append(HumanMessage(content=message))
            
            state = ChatState(
                messages=[HumanMessage(content=message)],
                agent_type="",
                history=self.conversation_history[user_id]
            )
            
            first = True
            async for msg, metadata in self.workflow.astream(state, stream_mode="messages"):
                if msg.content and not isinstance(msg, HumanMessage):
                    if msg.content not in [agent_type for agent_type in AgentType]:
                        yield {"content": msg.content}
                    # print(f"Yielding content chunk: {msg.content}")

                if isinstance(msg, AIMessageChunk):
                    if first:
                        gathered = msg
                        first = False
                    else:
                        gathered = gathered + msg

                    # Handle any tool calls if present
                    if msg.tool_call_chunks:
                        print(f"Tool calls: {gathered.tool_calls}")

        except Exception as e:
            print(f"Error in generate_response: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))