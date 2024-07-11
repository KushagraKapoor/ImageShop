from transformers import pipeline

# Initialize the summarizer
def initialize():
    return pipeline('summarization')
