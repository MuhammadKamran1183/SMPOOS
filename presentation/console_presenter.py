class ConsolePresenter:
    def display_summary(self, summary):
        print(f"Locations loaded: {summary['locations']}")
        print(f"Routes loaded: {summary['routes']}")
        print(f"Notifications loaded: {summary['notifications']}")
        print(f"Users loaded: {summary['users']}")
