"""
Extract structured laptop specifications from product titles using LangChain and Gemini.
Processes ALL titles in a single API call for efficiency.
"""
import os
import pandas as pd
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

load_dotenv()


class LaptopSpecs(BaseModel):
    """Structured laptop specifications extracted from product title."""
    sl_no: int = Field(description="Serial number of the laptop (from input)")
    product_name: str = Field(description="Short product name (brand + model), e.g. 'HP 15', 'ASUS Vivobook Go 14'")
    processor: str | None = Field(default=None, description="Processor name, e.g. 'Intel Core i3-1315U', 'AMD Ryzen 3 7320U'")
    ram: str | None = Field(default=None, description="RAM specification, e.g. '8GB DDR4', '16GB LPDDR5'")
    storage: str | None = Field(default=None, description="Storage specification, e.g. '512GB SSD', '128GB eMMC'")
    display: str | None = Field(default=None, description="Display size and type, e.g. '15.6\" FHD IPS', '14\" OLED'")
    gpu: str | None = Field(default=None, description="Graphics card, e.g. 'NVIDIA RTX 3050', 'AMD Radeon'. Use None for integrated graphics unless explicitly mentioned")
    os: str | None = Field(default=None, description="Operating system, e.g. 'Windows 11', 'Chrome OS', 'Android 15'")
    weight: str | None = Field(default=None, description="Weight, e.g. '1.5kg', '990 Grams'")
    color: str | None = Field(default=None, description="Color, e.g. 'Silver', 'Grey', 'Black'")


class LaptopSpecsList(BaseModel):
    """List of laptop specifications for batch processing."""
    laptops: list[LaptopSpecs] = Field(description="List of extracted laptop specifications")


def extract_specs_from_titles(
    input_csv: str = 'data/amazon_laptops.csv',
    output_csv: str = 'data/amazon_laptops_structured.csv'
) -> pd.DataFrame:
    """
    Extract structured specifications from laptop titles using Gemini.
    Processes ALL titles in a SINGLE API call.
    
    Args:
        input_csv: Path to input CSV with 'Title' column
        output_csv: Path to save the structured output
    
    Returns:
        DataFrame with extracted specifications
    """
    # Load data
    df = pd.read_csv(input_csv)
    print(f"Loaded {len(df)} laptops from {input_csv}")
    
    # Prepare input: Create a numbered list of titles
    titles_text = "\n".join([
        f"{row['SL No']}. {row['Title']}" 
        for _, row in df.iterrows()
    ])
    
    print(f"Total input size: {len(titles_text)} characters")
    
    # Initialize Gemini model with structured output
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")
    
    # Create structured output chain for batch processing
    structured_llm = llm.with_structured_output(LaptopSpecsList)
    
    # Prompt template for batch processing
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
You are an expert at extracting laptop specifications from Amazon product titles.

For EACH laptop title in the list below, extract:
- sl_no: The serial number at the start of each line
- product_name: Short brand + model name only (e.g., 'HP 15', 'ASUS Vivobook Go 14')
- processor: CPU model (e.g., 'Intel Core i3-1315U', 'AMD Ryzen 3 7320U')
- ram: Memory size and type (e.g., '8GB DDR4', '16GB LPDDR5')
- storage: Storage capacity and type (e.g., '512GB SSD', '128GB eMMC')
- display: Screen size and type (e.g., '15.6" FHD IPS', '14" OLED')
- gpu: Discrete graphics only (e.g., 'NVIDIA RTX 3050'). Use null for integrated graphics.
- os: Operating system (e.g., 'Windows 11', 'Chrome OS', 'Android 15')
- weight: Device weight (e.g., '1.5kg', '990g')
- color: Device color (e.g., 'Silver', 'Grey', 'Black')

IMPORTANT:
- Process ALL {count} laptops in the list
- If a field is not mentioned in the title, use null
- Be precise - extract exactly what's mentioned, don't infer or guess
- Return results in the same order as input"""),
        ("human", "{titles}")
    ])
    
    chain = prompt | structured_llm
    
    # Single API call to process all titles
    print("Calling Gemini API (single batch request)...")
    result = chain.invoke({
        "titles": titles_text,
        "count": len(df)
    })
    
    print(f"Received {len(result.laptops)} laptop specifications")
    
    # Convert to DataFrame
    specs_df = pd.DataFrame([laptop.model_dump() for laptop in result.laptops])
    
    # Merge with original data (prices, ratings, links)
    original_cols = df[['SL No', 'Current Price', 'MRP', 'Rating', 'Link']].copy()
    original_cols.columns = ['sl_no', 'current_price', 'mrp', 'rating', 'link']
    
    # Merge on sl_no
    output_df = specs_df.merge(original_cols, on='sl_no', how='left')
    
    # Reorder columns
    column_order = [
        'sl_no', 'product_name', 'processor', 'ram', 'storage', 'display',
        'gpu', 'os', 'weight', 'color', 'current_price', 'mrp', 'rating', 'link'
    ]
    output_df = output_df[column_order]
    
    # Save to CSV
    output_df.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"\nSaved structured data to {output_csv}")
    
    return output_df


if __name__ == '__main__':
    # Make sure GOOGLE_API_KEY is set
    if not os.environ.get('GOOGLE_API_KEY'):
        print("Please set GOOGLE_API_KEY environment variable")
        print("You can get an API key from https://aistudio.google.com/apikey")
        exit(1)
    
    df = extract_specs_from_titles()
    print("\nSample output (first 10 rows):")
    print(df[['sl_no', 'product_name', 'processor', 'ram', 'storage', 'display']].head(10).to_string())
    print(f"\nTotal laptops processed: {len(df)}")
