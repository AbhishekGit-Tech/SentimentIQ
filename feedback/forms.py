from django import forms

from .csv_utils import MAX_FILE_MB


class ManualFeedbackForm(forms.Form):
    text = forms.CharField(
        label="Feedback",
        min_length=3,
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 5, "placeholder": "e.g. Phone camera is amazing but battery is terrible"}),
    )


class CSVUploadForm(forms.Form):
    file = forms.FileField(label="CSV file")
    text_column = forms.CharField(label="Feedback column (optional)", required=False,
                                  help_text="Leave blank to auto-detect.")
    date_column = forms.CharField(label="Date column (optional)", required=False,
                                  help_text="Used for trends. Blank = auto-detect, or upload time if none found.")

    def clean_file(self):
        f = self.cleaned_data["file"]
        if not f.name.lower().endswith(".csv"):
            raise forms.ValidationError("Please upload a .csv file.")
        if f.size > MAX_FILE_MB * 1024 * 1024:
            raise forms.ValidationError(f"File is too large (max {MAX_FILE_MB} MB).")
        return f