class Book(BaseModel):
    """Book data model with validation."""
    
    url: str = Field(..., description="Book page URL")
    title: str = Field(..., min_length=1, description="Book title")
    description: Optional[str] = Field(None, description="Book description")
    category: str = Field(..., description="Book category")
    price_excl_tax: float = Field(..., gt=0, description="Price excluding tax")
    price_incl_tax: float = Field(..., gt=0, description="Price including tax")
    availability: str = Field(..., description="Availability status")
    num_reviews: int = Field(..., ge=0, description="Number of reviews")
    image_url: str = Field(..., description="Book cover image URL")
    rating: int = Field(..., ge=1, le=5, description="Star rating (1-5)")
    
    # Metadata
    crawl_timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="active", description="Book status")
    content_hash: Optional[str] = Field(None, description="Hash for change detection")
    raw_html: Optional[str] = Field(None, description="Raw HTML backup")
    
    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        """Ensure rating is between 1 and 5."""
        if not 1 <= v <= 5:
            raise ValueError(f"Rating must be between 1 and 5, got {v}")
        return v
    
    @field_validator('price_excl_tax', 'price_incl_tax')
    @classmethod
    def validate_price(cls, v):
        """Ensure price is positive."""
        if v <= 0:
            raise ValueError(f"Price must be positive, got {v}")
        return round(v, 2)
    
    @field_validator('title', 'category')
    @classmethod
    def strip_whitespace(cls, v):
        """Remove leading/trailing whitespace."""
        return v.strip() if v else v
    
    def generate_content_hash(self) -> str:
        """
        Generate a hash of key content fields for change detection.
        Changes in price, availability, or reviews will change the hash.
        """
        content = {
            "title": self.title,
            "price_excl_tax": self.price_excl_tax,
            "price_incl_tax": self.price_incl_tax,
            "availability": self.availability,
            "num_reviews": self.num_reviews,
            "rating": self.rating
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def to_dict(self) -> dict:
        """Convert model to dictionary for MongoDB storage."""
        data = self.model_dump()
        # Generate content hash if not present
        if not data.get('content_hash'):
            data['content_hash'] = self.generate_content_hash()
        return data
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

