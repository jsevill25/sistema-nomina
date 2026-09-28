from .common import *

class CorporateThemeManager:
    """Gestor de temas corporativos profesionales y modernos para ttk."""

    TEMAS = {
        "Corporativo Ejecutivo (Azul Petróleo)": {
            "bg": "#f4f6f9",
            "card_bg": "#ffffff",
            "text": "#2c3e50",
            "primary": "#1e3d59",
            "primary_active": "#173046",
            "accent": "#17b978",
            "border": "#d2d6dc",
            "header_bg": "#1e3d59",
            "header_fg": "#ffffff"
        },
        "Gris Ejecutivo Oscuro (Modo Noche)": {
            "bg": "#1e2229",
            "card_bg": "#282c34",
            "text": "#abb2bf",
            "primary": "#3a3f4b",
            "primary_active": "#4b5263",
            "accent": "#61afef",
            "border": "#4b5263",
            "header_bg": "#21252b",
            "header_fg": "#61afef"
        },
        "Corporativo Grafito & Oro (Ejecutivo)": {
            "bg": "#f8f9fa",
            "card_bg": "#ffffff",
            "text": "#212529",
            "primary": "#2d3748",
            "primary_active": "#1a202c",
            "accent": "#d69e2e",
            "border": "#cbd5e0",
            "header_bg": "#2d3748",
            "header_fg": "#ffffff"
        }
    }

    @classmethod
    def aplicar_tema(cls, root_window, nombre_tema: str):
        if nombre_tema not in cls.TEMAS:
            nombre_tema = "Corporativo Ejecutivo (Azul Petróleo)"

        t = cls.TEMAS[nombre_tema]
        style = ttk.Style(root_window)
        try:
            style.theme_use('clam')
        except Exception:
            pass

        # Configuración general de widgets estándar ttk
        style.configure('.',
                        background=t["bg"],
                        foreground=t["text"],
                        font=('Segoe UI', 10))

        style.configure('TFrame', background=t["bg"])
        style.configure('TLabelframe', background=t["bg"], foreground=t["primary"], bordercolor=t["border"])
        style.configure('TLabelframe.Label', background=t["bg"], foreground=t["primary"], font=('Segoe UI', 10, 'bold'))

        style.configure('TLabel', background=t["bg"], foreground=t["text"], font=('Segoe UI', 10))
        style.configure('TButton',
                        background=t["primary"],
                        foreground="#ffffff",
                        font=('Segoe UI', 10, 'bold'),
                        borderwidth=1,
                        focusthickness=3,
                        focuscolor=t["accent"])
        style.map('TButton',
                  background=[('active', t["primary_active"]), ('pressed', t["primary"])],
                  foreground=[('active', '#ffffff')])

        style.configure('TEntry', fieldbackground=t["card_bg"], foreground=t["text"], bordercolor=t["border"])
        style.configure('TCombobox', fieldbackground=t["card_bg"], background=t["primary"], foreground=t["text"])
        style.configure('TNotebook', background=t["bg"], borderwidth=0)
        style.configure('TNotebook.Tab', background=t["primary"], foreground="#ffffff", padding=[12, 6], font=('Segoe UI', 9, 'bold'))
        style.map('TNotebook.Tab',
                  background=[('selected', t["accent"]), ('active', t["primary_active"])],
                  foreground=[('selected', '#ffffff'), ('active', '#ffffff')])

        style.configure('Treeview',
                        background=t["card_bg"],
                        foreground=t["text"],
                        fieldbackground=t["card_bg"],
                        rowheight=26,
                        font=('Segoe UI', 9))
        style.configure('Treeview.Heading',
                        background=t["header_bg"],
                        foreground=t["header_fg"],
                        font=('Segoe UI', 9, 'bold'))
        style.map('Treeview', background=[('selected', t["accent"])], foreground=[('selected', '#ffffff')])
