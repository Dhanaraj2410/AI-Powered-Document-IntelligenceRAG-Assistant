import re


class CleanerService:

    @staticmethod
    def clean_text(text: str | None) -> str:
        """
        Cleans and normalizes extracted PDF text by removing redundant whitespace,
        multiple newlines, and non-printable control characters.
        """
        if not text:
            return ""

        # Remove control characters except standard whitespace
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

        # Replace multiple horizontal spaces/tabs with single space
        text = re.sub(r'[ \t]+', ' ', text)

        # Replace 3 or more consecutive newlines with 2 newlines
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Strip leading and trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        cleaned_text = '\n'.join(lines).strip()

        return cleaned_text
