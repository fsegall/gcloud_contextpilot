from GitContextManager import GitContextManager

manager = GitContextManager()

diff = manager.show_diff()
summary = manager.summarize_diff_for_commit(diff)
manager.commit_with_llm_message(summary)
