from django import forms

class QueryForm(forms.Form):
    query = forms.CharField(
        label='Your question',
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ask a question about industrial safety...'
        })
    )
    
    top_k = forms.IntegerField(
        label='Number of results',
        min_value=1,
        max_value=10,
        initial=5,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    mode_choices = [
        ('baseline', 'Baseline (Vector Search Only)'),
        ('reranked', 'Reranked (Hybrid Approach)')
    ]
    
    mode = forms.ChoiceField(
        label='Search mode',
        choices=mode_choices,
        initial='reranked',
        widget=forms.Select(attrs={'class': 'form-control'})
    )