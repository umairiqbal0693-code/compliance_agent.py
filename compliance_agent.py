import streamlit as st
import anthropic
import json
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="AI Compliance Screening Agent",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_result' not in st.session_state:
    st.session_state.current_result = None

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .risk-high {
        background-color: #fee;
        border-left: 4px solid #f00;
        padding: 1rem;
        border-radius: 5px;
    }
    .risk-medium {
        background-color: #ffc;
        border-left: 4px solid #fa0;
        padding: 1rem;
        border-radius: 5px;
    }
    .risk-low {
        background-color: #eff;
        border-left: 4px solid #09f;
        padding: 1rem;
        border-radius: 5px;
    }
    .risk-clear {
        background-color: #efe;
        border-left: 4px solid #0f0;
        padding: 1rem;
        border-radius: 5px;
    }
    .finding-card {
        border: 1px solid #ddd;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

def get_api_key():
    """Get API key from environment or user input"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        api_key = st.sidebar.text_input(
            "Enter Anthropic API Key",
            type="password",
            help="Get your API key from https://console.anthropic.com/"
        )
    return api_key

def perform_screening(entity, search_type, api_key):
    """Perform compliance screening using Anthropic API"""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        # Build prompt based on search type
        search_context = "controversy scandal investigation lawsuit sanction fine penalty fraud" if search_type == "comprehensive" else "negative news"
        
        prompt = f"""You are a compliance screening AI agent. Search for negative news, controversies, legal issues, sanctions, and regulatory problems related to: "{entity}"

Please search comprehensively and then provide a structured analysis in JSON format with the following structure:
{{
  "riskLevel": "HIGH|MEDIUM|LOW|CLEAR",
  "summary": "Brief overview of findings",
  "findings": [
    {{
      "category": "category name",
      "severity": "HIGH|MEDIUM|LOW",
      "title": "finding title",
      "description": "detailed description",
      "date": "date if available",
      "source": "source name",
      "url": "source url if available"
    }}
  ],
  "recommendations": ["list of recommendations"]
}}

Search thoroughly and provide accurate, factual information only. If no significant negative news is found, indicate CLEAR risk level."""

        # Make API call with web search
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search"
            }],
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Extract response
        full_response = ""
        for block in message.content:
            if block.type == "text":
                full_response += block.text
        
        # Parse JSON from response
        try:
            json_start = full_response.find('{')
            json_end = full_response.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = full_response[json_start:json_end]
                results = json.loads(json_str)
            else:
                raise ValueError("No JSON found")
        except:
            # Fallback structure
            results = {
                "riskLevel": "MEDIUM",
                "summary": full_response[:300] if full_response else "Unable to parse response",
                "findings": [{
                    "category": "General",
                    "severity": "MEDIUM",
                    "title": "Analysis Results",
                    "description": full_response or "No detailed findings available",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "source": "AI Analysis"
                }],
                "recommendations": ["Review the detailed findings", "Conduct further due diligence"]
            }
        
        # Add metadata
        results['entity'] = entity
        results['timestamp'] = datetime.now().isoformat()
        results['searchType'] = search_type
        
        return results
        
    except Exception as e:
        return {
            "entity": entity,
            "timestamp": datetime.now().isoformat(),
            "riskLevel": "ERROR",
            "summary": f"Error during screening: {str(e)}",
            "findings": [],
            "recommendations": ["Check API key", "Verify network connection", "Try again"]
        }

def display_risk_badge(risk_level):
    """Display colored risk level badge"""
    colors = {
        "HIGH": ("🔴", "risk-high"),
        "MEDIUM": ("🟡", "risk-medium"),
        "LOW": ("🔵", "risk-low"),
        "CLEAR": ("🟢", "risk-clear"),
        "ERROR": ("⚪", "")
    }
    icon, css_class = colors.get(risk_level, ("⚪", ""))
    return f'<div class="{css_class}"><h2>{icon} Risk Level: {risk_level}</h2></div>'

def export_results(results):
    """Export results as JSON"""
    return json.dumps(results, indent=2)

# Main UI
st.markdown('<div class="main-header"><h1>🔍 AI Compliance Screening Agent</h1><p>Automated negative news screening powered by AI</p></div>', unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.header("Configuration")
    api_key = get_api_key()
    
    st.divider()
    st.header("Risk Categories")
    st.write("""
    - Financial Crime
    - Regulatory Violations
    - Sanctions
    - Corruption
    - Money Laundering
    - Fraud
    - Legal Issues
    - Reputational Risk
    """)
    
    st.divider()
    st.header("About")
    st.write("This tool performs automated compliance screening using AI-powered web search to identify potential risks.")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Screening Input")
    entity = st.text_input(
        "Entity Name",
        placeholder="e.g., ABC Corporation, John Smith, XYZ Bank",
        help="Enter the name of a person, company, or organization to screen"
    )
    
    search_type = st.selectbox(
        "Search Type",
        ["comprehensive", "basic"],
        format_func=lambda x: "Comprehensive (All risk categories)" if x == "comprehensive" else "Basic (General negative news)"
    )
    
    if st.button("🔍 Start Screening", type="primary", disabled=not api_key or not entity):
        if not api_key:
            st.error("Please provide an Anthropic API key")
        else:
            with st.spinner("Screening in progress..."):
                results = perform_screening(entity, search_type, api_key)
                st.session_state.current_result = results
                st.session_state.history.insert(0, results)
                if len(st.session_state.history) > 10:
                    st.session_state.history = st.session_state.history[:10]
                st.rerun()

with col2:
    st.header("Recent Screenings")
    if st.session_state.history:
        for idx, item in enumerate(st.session_state.history[:5]):
            if st.button(
                f"{item.get('entity', 'Unknown')} - {item.get('riskLevel', 'N/A')}",
                key=f"history_{idx}",
                use_container_width=True
            ):
                st.session_state.current_result = item
                st.rerun()
    else:
        st.info("No screening history yet")

# Display results
if st.session_state.current_result:
    st.divider()
    results = st.session_state.current_result
    
    # Header with export
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("Screening Results")
    with col2:
        st.download_button(
            "📥 Export JSON",
            data=export_results(results),
            file_name=f"compliance-screening-{results['entity'].replace(' ', '-')}-{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
    
    # Risk level
    st.markdown(display_risk_badge(results['riskLevel']), unsafe_allow_html=True)
    st.write(f"**Entity:** {results['entity']}")
    st.write(f"**Screened:** {datetime.fromisoformat(results['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Summary
    st.subheader("Executive Summary")
    st.write(results.get('summary', 'No summary available'))
    
    # Findings
    if results.get('findings'):
        st.subheader("Detailed Findings")
        for idx, finding in enumerate(results['findings']):
            with st.expander(f"{finding.get('severity', 'N/A')} - {finding.get('title', 'Finding')}"):
                st.markdown(f"**Category:** {finding.get('category', 'N/A')}")
                st.markdown(f"**Severity:** {finding.get('severity', 'N/A')}")
                st.write(finding.get('description', 'No description'))
                
                col1, col2 = st.columns(2)
                with col1:
                    if finding.get('date'):
                        st.caption(f"📅 Date: {finding['date']}")
                with col2:
                    if finding.get('source'):
                        st.caption(f"📰 Source: {finding['source']}")
                
                if finding.get('url'):
                    st.link_button("🔗 View Source", finding['url'])
    
    # Recommendations
    if results.get('recommendations'):
        st.subheader("Recommendations")
        for rec in results['recommendations']:
            st.write(f"• {rec}")
