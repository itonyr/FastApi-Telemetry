from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry import trace
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Setup the FastAPI application
app = FastAPI()

# Database URL
DATABASE_URL = "postgresql+asyncpg://postgres:mysecretpassword@localhost:5432/test"

# Setup OpenTelemetry with Jaeger Exporter
resource = Resource(attributes={
    ResourceAttributes.SERVICE_NAME: "my-fastapi-service"
})

trace_provider = TracerProvider(resource=resource)
jaeger_exporter = JaegerExporter(agent_host_name="localhost", agent_port=6831)
span_processor = BatchSpanProcessor(jaeger_exporter)
trace_provider.add_span_processor(span_processor)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app, tracer_provider=trace_provider)

# Set up SQLAlchemy async engine and session
Base = declarative_base()

class Post(Base):
    __tablename__ = 'test_table'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    created_at = Column(String)

# Create the async engine
engine = create_async_engine(DATABASE_URL, echo=True)
SQLAlchemyInstrumentor().instrument()  # Instrument SQLAlchemy
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Create the tables on startup
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Dependency to get the async session
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

@app.get("/")
async def read_root():
    return {"message": "Hello, OpenTelemetry with FastAPI and Jaeger!"}

@app.get("/posts/{post_id}")
async def fetch_post(post_id: int, db: AsyncSession = Depends(get_db)):
    with trace.get_tracer(__name__).start_as_current_span("fetch_post_api_call") as api_span:
        api_span.set_attribute("http.method", "GET")
        api_span.set_attribute("http.route", "/posts/{post_id}")

        async with db.begin():
            with trace.get_tracer(__name__).start_as_current_span("fetch_post_from_db") as db_span:
                db_span.set_attribute("db.system", "postgresql")
                db_span.set_attribute("db.statement", f"SELECT * FROM test_table WHERE id={post_id}")

                try:
                    result = await db.execute(select(Post).where(Post.id == post_id))
                    post = result.scalar_one_or_none()

                    if post:
                        return {
                            "id": post.id,
                            "name": post.name,
                            "created_at": post.created_at,
                        }
                    else:
                        raise HTTPException(status_code=404, detail="Post not found")
                except Exception as e:
                    db_span.record_exception(e)
                    raise
