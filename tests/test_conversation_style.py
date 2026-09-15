import unittest
from conversation_style import CHAT_STYLE, conversation_instruction
from bot import SYSTEM


class StyleTests(unittest.TestCase):
    def test_greetings_stay_short_even_in_long_mode(self):
        for text in ('Ciao!', 'ciao @giacomino_bot', 'Grazie', 'ok'):
            for mode in ('short', 'long'):
                prompt = conversation_instruction(text, mode)
                self.assertIn('una sola frase', prompt)
                self.assertNotIn('250 parole', prompt)
                self.assertTrue(prompt.endswith(text))

    def test_short_technical_question_can_still_be_explained(self):
        prompt = conversation_instruction('spiegami PostgreSQL', 'long')
        self.assertIn('approfondire', prompt)
        self.assertNotIn('È un saluto', prompt)

    def test_short_mode_has_no_padding_quota(self):
        prompt = conversation_instruction('non hai capito un cazzo', 'short')
        self.assertIn('una o due frasi', prompt)
        self.assertIn('nessun minimo', prompt)
        self.assertNotIn('40-100', prompt)

    def test_style_is_applied_and_does_not_require_human_impersonation(self):
        self.assertIn(CHAT_STYLE, SYSTEM)
        self.assertIn('sii onesto sulla tua natura di bot', CHAT_STYLE)
        self.assertIn('Niente emoji decorative', CHAT_STYLE)
