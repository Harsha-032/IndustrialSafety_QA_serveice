from django.db import models

class Document(models.Model):
    title = models.CharField(max_length=500)
    url = models.URLField()
    processed = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title

class DocumentChunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    chunk_text = models.TextField()
    chunk_index = models.IntegerField()
    embedding = models.BinaryField(null=True, blank=True)
    
    class Meta:
        unique_together = ('document', 'chunk_index')
    
    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"