import os
from jinja2 import Environment, FileSystemLoader, select_autoescape

class PromptManager:
    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            # Assume templates are in backend/prompts relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            templates_dir = os.path.join(current_dir, "..", "..", "prompts")
        
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape()
        )

    def render_prompt(self, template_path: str, **kwargs) -> str:
        """
        Render a Jinja2 template with provided arguments.
        
        Args:
            template_path: Path to the template relative to templates_dir
            **kwargs: Arguments to pass to the template
        """
        template = self.env.get_template(template_path)
        return template.render(**kwargs)

# Global instance for easy use
_prompt_manager = None

def get_prompt_manager() -> PromptManager:
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
