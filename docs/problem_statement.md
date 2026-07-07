# BE Computer Science / AI & ML Final Year Project Proposal

## Project Title

**Supply Chain Intelligence Co-Pilot using LangGraph, MCP, Knowledge
Base, Text-to-SQL and API Integration**

------------------------------------------------------------------------

## 1. Project Overview

Supply chain teams need to check order status, shipment status,
inventory availability, invoice status, delivery delays and customer SLA
details from many different systems.

Normally, users manually check ERP, WMS, TMS, courier portals, Excel
files, SOP documents and customer contracts. This creates delay, manual
dependency and poor visibility.

This project proposes an **Agentic AI Supply Chain Co-Pilot** that can
answer supply chain questions using:

-   Knowledge Base RAG
-   Text-to-SQL
-   REST API integration
-   LangGraph agent orchestration
-   MCP tool connectivity

The user can ask business questions in natural language, and the system
will automatically decide whether to search documents, query a database,
call APIs, or apply business rules.

------------------------------------------------------------------------

## 2. Problem Statement

Supply chain data is distributed across multiple systems such as ERP,
WMS, TMS, shipment tracking portals and document repositories.

Business users face challenges such as:

-   No single place to check order and shipment status
-   Manual dependency on operations and IT teams
-   Delay in customer response
-   Difficulty finding SOP and SLA rules
-   Manual SQL report generation
-   No intelligent recommendation for delay resolution

There is a need for an AI-based system that can connect enterprise
knowledge, structured databases and external APIs into one
conversational interface.

------------------------------------------------------------------------

## 3. Project Objective

The objective of this project is to build an AI-powered Supply Chain
Co-Pilot that can:

-   Understand natural language user questions
-   Retrieve answers from the company knowledge base
-   Convert business questions into SQL
-   Query a PostgreSQL database
-   Call external shipment and ERP APIs
-   Apply SLA and business rules
-   Generate a final answer with recommended action
-   Maintain audit logs for every query and tool call

------------------------------------------------------------------------

## 4. Why LangGraph and MCP Are Used

### LangGraph Usage

LangGraph is used for agent workflow orchestration.

It controls:

-   Supervisor Agent
-   Intent classification
-   Agent routing
-   State management
-   Multi-step execution
-   Retry handling
-   Human-in-the-loop option
-   Final response generation

### MCP Usage

MCP is used for standardized tool connectivity.

It connects agents with:

-   PostgreSQL database
-   Vector database
-   Knowledge base
-   ERP API
-   Shipment tracking API
-   Inventory API
-   Document repository

**LangGraph controls the intelligence flow, while MCP provides tool
access.**

------------------------------------------------------------------------

## 5. System Architecture Diagram

``` mermaid
flowchart TD
    A["User<br/>Supply Chain Manager"] --> B["Angular Web Chat UI<br/>Ask business question"]
    B --> C["Java Spring Boot API<br/>Auth, session, audit"]
    C --> D["Python FastAPI AI Layer"]
    D --> E["LangGraph Supervisor Agent<br/>Intent detection, routing, state, retry"]

    E --> F["Knowledge Base Agent"]
    E --> G["Text-to-SQL Agent"]
    E --> H["API Status Agent"]

    F --> I["MCP KB Tool"]
    G --> J["MCP DB Tool"]
    H --> K["MCP API Tool"]

    I --> L["Vector Database<br/>Chroma / pgvector"]
    J --> M["PostgreSQL<br/>Orders, stock"]
    K --> N["ERP / WMS /<br/>Shipment APIs"]

    L --> O["Business Rule Agent<br/>SLA, delay, escalation"]
    M --> O
    N --> O

    O --> P["Final Response Agent"]
```

------------------------------------------------------------------------

## 6. Main Use Case

### Use Case Name

**Order and Shipment Status Intelligence**

### User Question

> "Where is customer order SO-45892? Why is it delayed and what action
> should we take?"

### System Execution

1.  LangGraph Supervisor receives the question.
2.  Intent Detection Agent identifies it as order status and delay
    analysis.
3.  Text-to-SQL Agent queries order, invoice and inventory data.
4.  API Status Agent calls the shipment tracking API.
5.  Knowledge Base Agent checks SLA and delay-handling SOP.
6.  Business Rule Agent checks for an SLA breach.
7.  Final Response Agent gives the answer and recommended action.

------------------------------------------------------------------------

## 7. Sample Final Output

**Order SO-45892 has been dispatched from the warehouse.**

### Current Shipment Status

The shipment is currently at Chennai Port and is under customs hold.

### Reason for Delay

The shipment API shows an HS code mismatch during customs validation.

### Impact

-   Promised delivery date: **3 July 2026**
-   Revised ETA: **9 July 2026**
-   Delay: **6 days**
-   Result: **Customer SLA breach**

### Recommended Action

1.  Verify the HS code in the commercial invoice.
2.  Send the corrected document to the customs broker.
3.  Escalate to the logistics manager.
4.  Notify the customer with the revised ETA.

------------------------------------------------------------------------

## 8. Major Modules

### 8.1 Angular Web UI

-   Chat interface
-   Query history
-   Suggested supply chain questions
-   Result display
-   Audit view

### 8.2 Java Spring Boot Backend

-   User authentication
-   API gateway
-   Session management
-   Audit logging
-   Request routing to the AI layer

### 8.3 Python FastAPI AI Layer

-   Connects the backend with LangGraph
-   Manages AI workflows
-   Calls the LLM
-   Handles agent responses

### 8.4 LangGraph Supervisor

-   Controls agent execution
-   Maintains state
-   Decides which agent to call
-   Handles retry and fallback
-   Combines the final response

### 8.5 Knowledge Base Agent

-   Uses RAG
-   Searches SOP, SLA, policy and process documents
-   Retrieves relevant context
-   Gives source-based answers

### 8.6 Text-to-SQL Agent

-   Converts user questions into SQL
-   Queries PostgreSQL
-   Returns structured business data
-   Validates SQL before execution

### 8.7 API Status Agent

-   Calls the shipment tracking API
-   Calls ERP/WMS/TMS APIs
-   Parses JSON responses
-   Returns real-time status

### 8.8 Business Rule Agent

-   Checks SLA breaches
-   Checks delay reasons
-   Checks escalation rules
-   Suggests corrective action

### 8.9 MCP Server

-   Provides standard tool access
-   Connects agents to the database, APIs and knowledge base
-   Improves security and reusability

------------------------------------------------------------------------

## 9. Technology Stack

  Layer                 Technology
  --------------------- ---------------------------
  Frontend              Angular
  Backend               Java Spring Boot
  AI Service            Python FastAPI
  Agent Framework       LangGraph
  Tool Connectivity     MCP Server and MCP Client
  LLM                   Qwen / Llama / GPT
  Knowledge Base        RAG
  Vector Database       ChromaDB / pgvector
  Relational Database   PostgreSQL
  API Integration       REST API
  Authentication        JWT / OAuth2
  Monitoring            OpenTelemetry / Grafana
  Deployment            Docker

------------------------------------------------------------------------

## 10. Database Tables

-   `customers`
-   `sales_orders`
-   `order_items`
-   `inventory`
-   `warehouse`
-   `shipment`
-   `invoice`
-   `payment`
-   `carrier_tracking`
-   `audit_log`
-   `knowledge_documents`

------------------------------------------------------------------------

## 11. Example Text-to-SQL Query

### User Asks

> "Show delayed orders from Chennai warehouse."

### Generated SQL

``` sql
SELECT
    order_no,
    customer_name,
    warehouse_location,
    promised_delivery_date,
    current_status
FROM sales_orders
WHERE warehouse_location = 'Chennai'
  AND current_status = 'Delayed';
```

------------------------------------------------------------------------

## 12. Example APIs

### Shipment Tracking API

``` http
GET /api/shipment/status/{trackingNumber}
```

### Inventory API

``` http
GET /api/inventory/{sku}
```

### ERP Order API

``` http
GET /api/order/{orderNumber}
```

------------------------------------------------------------------------

## 13. Expected Benefits

-   Faster order status checking
-   Reduced manual work
-   Self-service supply chain query system
-   Better customer response time
-   Real-time shipment visibility
-   Automatic SLA checking
-   Intelligent recommendation for delay resolution
-   Practical use of Agentic AI in supply chain

------------------------------------------------------------------------

## 14. Project Deliverables

-   Angular UI
-   Spring Boot backend
-   Python FastAPI AI service
-   LangGraph workflow
-   MCP server tools
-   PostgreSQL database
-   Knowledge base documents
-   REST API simulation
-   Project report
-   PPT presentation
-   Demo video

------------------------------------------------------------------------

## 15. Two-Week Project Plan

  Timeline    Activity
  ----------- ----------------------------------------------
  Day 1--2    Requirement analysis and architecture design
  Day 3--4    Database design and dummy data creation
  Day 5--6    Angular UI and Spring Boot API development
  Day 7--8    Knowledge Base RAG setup
  Day 9--10   Text-to-SQL and PostgreSQL integration
  Day 11      API Status Agent development
  Day 12      LangGraph supervisor workflow
  Day 13      MCP tool integration and testing
  Day 14      Documentation, PPT and demo preparation

------------------------------------------------------------------------

## 16. Expected Learning Outcomes

Students will learn:

-   Agentic AI architecture
-   LangGraph workflow design
-   MCP-based tool connectivity
-   RAG-based knowledge retrieval
-   Text-to-SQL development
-   REST API integration
-   PostgreSQL database design
-   Spring Boot backend development
-   Angular frontend development
-   Enterprise AI system design

------------------------------------------------------------------------

## 17. Future Enhancements

-   SAP / Microsoft Dynamics 365 integration
-   WhatsApp-based supply chain assistant
-   Voice-based query system
-   Predictive delay analytics
-   Demand forecasting
-   Automated customer notification
-   Control tower dashboard
-   Multi-language support

------------------------------------------------------------------------

## 18. Conclusion

This project is suitable for BE Computer Science / AI & ML students
because it combines modern AI concepts with a real business problem in
supply chain.

The project demonstrates how LangGraph can be used for agent
orchestration and MCP can be used for connecting databases, APIs and
knowledge sources. It is practical, industry-relevant and can be
completed as a strong final-year project prototype.
