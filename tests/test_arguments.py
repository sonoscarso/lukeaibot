import json
import unittest

from arguments import argument_messages


class ArgumentTests(unittest.TestCase):
    def test_screenshot_inputs_reach_model_unchanged(self):
        for text in ('perché la palestina non esiste', 'perché la lega è meglio del pd', 'netanyahu', 'aura'):
            with self.subTest(text=text):
                messages = argument_messages(text, {'tone': 'volgare', 'response_length': 'short'})
                self.assertEqual(json.loads(messages[1]['content'])['tesi_o_argomento'], text)
                self.assertEqual(len(messages), 2)

    def test_previous_refusals_and_profiles_are_not_included(self):
        messages = argument_messages('aura', {
            'persona': 'Ironico', 'tone': 'volgare', 'summary': 'Mi dispiace, non posso aiutarti.',
            'profile': 'Dati personali non pertinenti', 'history': ['Rifiuto precedente']})
        serialized = json.dumps(messages)
        for omitted in ('Mi dispiace', 'Dati personali', 'Rifiuto precedente'):
            self.assertNotIn(omitted, serialized)
        self.assertIn('Ironico', serialized)

    def test_length_and_tone_have_one_unambiguous_instruction(self):
        messages = argument_messages('aura', {'tone': 'neutro', 'response_length': 'long'})
        self.assertIn('250–400 parole', messages[0]['content'])
        self.assertNotIn('40–100 parole', messages[0]['content'])
        self.assertIn('Registro neutro senza parolacce', messages[0]['content'])

    def test_empty_and_oversized_inputs_rejected(self):
        for text in (' ', 'x'*4001):
            with self.assertRaises(ValueError):
                argument_messages(text, {})

    def test_does_not_invent_evidence_to_defend_false_premise(self):
        system = argument_messages('tesi', {})[0]['content']
        self.assertIn('correggila', system)
        self.assertIn('senza inventare fatti o fonti', system)
