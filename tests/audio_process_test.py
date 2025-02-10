import unittest
from src.audio_processor.audio_processor import align_audio_with_script

test_audio_path = "Tests/test_audio.wav"
test_script_path = "Tests/test_script.txt"


class TestAudioScriptAlignment(unittest.TestCase):

    def test_align_audio_with_script(self):
        audio_segments = [
            {
                'words': [
                    {'word': 'Hello', 'start': 0.5, 'end': 0.8},
                    {'word': 'world', 'start': 0.9, 'end': 1.2},
                ]
            },
            {
                'words': [
                    {'word': 'this', 'start': 1.3, 'end': 1.5},
                    {'word': 'id', 'start': 1.6, 'end': 1.7},
                    {'word': 'test', 'start': 2.0, 'end': 2.3}
                ]
            }
        ]

        # Dummy script lines
        script_path = "Tests/test_data/script.txt"

        # Expected output
        expected_output = [
            {
                'script_line': 'Hello world',
                'words': [
                    {'text': 'Hello', 'start': 0.5, 'end': 0.8},
                    {'text': 'world', 'start': 0.9, 'end': 1.2}
                ],
                'start': 0.5,
                'end': 1.2
            },
            {
                'script_line': 'This is a test',
                'words': [
                    {'text': 'This', 'start': 1.3, 'end': 1.5},
                    {'text': 'id', 'start': 1.6, 'end': 1.7},
                    {'text': 'test', 'start': 2.0, 'end': 2.3}
                ],
                'start': 1.3,
                'end': 2.3
            }
        ]

        result = align_audio_with_script(script_path, audio_segments)
        self.assertEqual(result, expected_output)

# Run the test
if __name__ == '__main__':
    unittest.main()