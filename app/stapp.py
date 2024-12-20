import streamlit as st
from swarm import Swarm, Agent
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
import os

AGENT_TEMPLATES = {
    'general': "You are a helpful general assistant focused on providing clear, accurate information on any topic.",
    'coder': "You are an expert programmer who helps write, explain and debug code. You follow best practices and provide detailed explanations.",
    'analyst': "You are a data analyst focused on helping interpret data, create visualizations, and derive insights.",
    'teacher': "You are an expert teacher who explains complex topics in simple terms with examples and analogies.",
    'writer': "You are a skilled writer who helps with content creation, editing and writing improvement."
}

@dataclass
class AgentConfig:
    name: str
    instructions: str
    category: str
    functions: List = None
    
class SwarmUI:
    def __init__(self):
        self.client = Swarm()
        self.agents = {
            'general': {},
            'specialized': {},
            'custom': {}
        }
        self.setup_session_state()
        self.load_agents()
        
    def setup_session_state(self):
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'current_agent' not in st.session_state:
            st.session_state.current_agent = None
            
    def create_agent(self, name: str, instructions: str, category: str = 'custom', functions: List = None) -> Agent:
        if functions is None:
            functions = []
        agent = Agent(
            name=name,
            instructions=instructions,
            functions=functions
        )
        self.agents[category][name] = agent
        self.save_agents()
        return agent
    
    def create_from_template(self, name: str, template: str, category: str = 'general'):
        instructions = AGENT_TEMPLATES.get(template, "")
        return self.create_agent(name, instructions, category)
        
    def list_agents(self, category: Optional[str] = None) -> List[str]:
        if category:
            return list(self.agents[category].keys())
        return [name for category in self.agents.values() for name in category.keys()]
        
    def get_agent(self, name: str) -> Optional[Agent]:
        for category in self.agents.values():
            if name in category:
                return category[name]
        return None
        
    def remove_agent(self, name: str):
        for category in self.agents:
            if name in self.agents[category]:
                del self.agents[category][name]
                self.save_agents()
                break
                
    def save_agents(self):
        agents_data = {}
        for category, agents in self.agents.items():
            agents_data[category] = {
                name: {
                    'instructions': agent.instructions,
                    'functions': agent.functions
                } for name, agent in agents.items()
            }
        with open('agents.json', 'w') as f:
            json.dump(agents_data, f)
            
    def load_agents(self):
        try:
            with open('agents.json', 'r') as f:
                agents_data = json.load(f)
                for category, agents in agents_data.items():
                    for name, data in agents.items():
                        self.create_agent(
                            name, 
                            data['instructions'],
                            category,
                            data.get('functions', [])
                        )
        except FileNotFoundError:
            # Create default agents from templates
            for template_name, instructions in AGENT_TEMPLATES.items():
                self.create_agent(
                    f"{template_name.title()} Assistant",
                    instructions,
                    'general'
                )
                
    def process_message(self, user_input: str, agent: Agent, context_vars: Optional[Dict] = None):
        if not agent:
            st.error("Please select an agent first")
            return
            
        messages = [{"role": "user", "content": user_input}]
        
        with st.spinner("Processing..."):
            response = self.client.run(
                agent=agent,
                messages=messages,
                context_variables=context_vars,
                stream=True
            )
            
            message_buffer = ""
            message_container = st.empty()
            
            for chunk in response:
                if "delim" in chunk:
                    if chunk["delim"] == "start":
                        st.write(f"🔄 Agent {agent.name} is processing...")
                    continue
                    
                if "content" in chunk:
                    message_buffer += chunk["content"]
                    message_container.markdown(message_buffer)
                    
            st.session_state.messages.append({
                "role": "user",
                "content": user_input,
                "agent": agent.name
            })
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": message_buffer,
                "agent": agent.name
            })

def render_sidebar(swarm: SwarmUI):
    st.sidebar.title("Agent Management")
    
    # Create from template
    st.sidebar.subheader("Create from Template")
    template_name = st.sidebar.selectbox(
        "Select Template",
        options=list(AGENT_TEMPLATES.keys()),
        format_func=lambda x: x.title()
    )
    new_agent_name = st.sidebar.text_input("Agent Name")
    
    if st.sidebar.button("Create from Template"):
        if new_agent_name:
            swarm.create_from_template(new_agent_name, template_name)
            st.sidebar.success(f"Agent {new_agent_name} created!")
            st.rerun()
            
    # Custom agent creation
    st.sidebar.subheader("Create Custom Agent")
    custom_name = st.sidebar.text_input("Custom Agent Name")
    custom_instructions = st.sidebar.text_area("Custom Instructions")
    
    if st.sidebar.button("Create Custom Agent"):
        if custom_name and custom_instructions:
            swarm.create_agent(custom_name, custom_instructions, 'custom')
            st.sidebar.success(f"Custom agent {custom_name} created!")
            st.rerun()
            
def render_chat():
    st.title("OpenAI Swarm Agent Chat")
    
    swarm = SwarmUI()
    render_sidebar(swarm)
    
    # Agent listing and selection
    st.subheader("Available Agents")
    
    tabs = st.tabs(["General", "Specialized", "Custom"])
    
    for tab, category in zip(tabs, swarm.agents.keys()):
        with tab:
            for agent_name in swarm.list_agents(category):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{agent_name}**")
                    agent = swarm.get_agent(agent_name)
                    with st.expander("Instructions"):
                        st.write(agent.instructions)
                with col2:
                    if st.button("Select", key=f"select_{agent_name}"):
                        st.session_state.current_agent = agent
                with col3:
                    if st.button("Delete", key=f"delete_{agent_name}"):
                        swarm.remove_agent(agent_name)
                        if st.session_state.current_agent and st.session_state.current_agent.name == agent_name:
                            st.session_state.current_agent = None
                        st.rerun()
    
    # Chat interface
    st.subheader("Chat")
    
    if st.session_state.current_agent:
        st.write(f"**Current Agent**: {st.session_state.current_agent.name}")
        
        # Context variables
        with st.expander("Context Variables"):
            context_vars = {}
            col1, col2 = st.columns(2)
            with col1:
                var_name = st.text_input("Variable Name")
            with col2:    
                var_value = st.text_input("Value")
            
            if st.button("Add Variable"):
                if var_name and var_value:
                    context_vars[var_name] = var_value
        
        # Chat history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(f"**Agent**: {msg['agent']}")
                st.write(msg["content"])
                
        # User input
        user_input = st.chat_input("Type your message here...")
        if user_input:
            swarm.process_message(
                user_input, 
                st.session_state.current_agent,
                context_vars
            )
    else:
        st.info("Please select an agent to start chatting")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Swarm Agent Chat",
        page_icon="🤖",
        layout="wide"
    )
    render_chat()
