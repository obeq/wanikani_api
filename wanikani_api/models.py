import pprint

import dateutil.parser

from wanikani_api import constants
from wanikani_api.exceptions import UnknownResourceException


class Iterator:
    def __init__(self, current_page, api_request, max_results=None):
        self.current_page = current_page
        self.api_request = api_request
        self.max_results = max_results
        self.yielded_count = 0

    def _iter_page(self):
        while self.current_page is not None:
            yield self.current_page
            if self._has_next_page():
                self.current_page = self._get_next_page()

    def _keep_iterating(self):
        return (
            self.current_page is not None
            and self.max_results
            and self.yielded_count >= self.max_results
        )

    def _has_next_page(self):
        if (
            self.current_page is not None
            and self.current_page.next_page_url is not None
        ):
            return True
        return False

    def _iter_items(self):
        for page in self._iter_page():
            for item in page:
                # early break from page if we have set a limit.
                if self._limit_reached():
                    raise StopIteration
                self.yielded_count += 1
                yield item

    def __iter__(self):
        return self._iter_items()

    def _get_next_page(self):
        if self.current_page.next_page_url:
            return self.api_request(self.current_page.next_page_url)
        else:
            return None

    def _limit_reached(self):
        return self.max_results and self.yielded_count >= self.max_results


class Resource:
    def __init__(self, json_data):
        self.resource = json_data["object"]
        self._raw = json_data
        self.url = json_data["url"]
        self.data_updated_at = parse8601(json_data["data_updated_at"])
        # Some Resources do not have IDs.
        self.id = (
            None
            if self.resource in constants.RESOURCES_WITHOUT_IDS
            else json_data["id"]
        )
        self._resource = json_data["data"]

    def raw_json(self):
        return pprint.pformat(self._raw)


class Page(Resource):
    resource = "collection"

    def __init__(self, json_data):
        super().__init__(json_data)
        self.next_page_url = json_data["pages"]["next_url"]
        self.previous_page_url = json_data["pages"]["previous_url"]
        self.total_count = json_data["total_count"]
        self.data = [factory(item) for item in json_data["data"]]
        self._data_iterator = iter(json_data["data"])

    def __iter__(self):
        return self

    def __next__(self):
        item = next(self._data_iterator)
        resource = factory(item)
        return resource


class UserInformation(Resource):
    """
    This is a simple container for information returned from the ``/user/`` endpoint.
    """

    resource = "user"

    def __init__(self, json_data):
        super().__init__(json_data)
        self.username = self._resource["username"]  #: username
        self.level = self._resource["level"]  #: current wanikani level
        self.max_level_granted_by_subscription = self._resource[
            "max_level_granted_by_subscription"
        ]  #: maximum level granted by subscription.
        self.profile_url = self._resource["profile_url"]  #: Link to user's profile.
        self.started_at = parse8601(
            self._resource["started_at"]
        )  #: datetime at which the user signed up.
        self.subscribed = self._resource[
            "subscribed"
        ]  #: Whether or not the user is currently subscribed to wanikani.
        self.current_vacation_started_at = parse8601(
            self._resource["current_vacation_started_at"]
        )  #: datetime at which vacation was enabled on wanikani.

    def __str__(self):
        return "UserInformation{{ username:{}, level:{}, max_level_granted_by_subscription:{}, profile_url:{} started_at:{}, subscribed:{}, current_vacation_started_at:{} }}".format(
            self.username,
            self.level,
            self.max_level_granted_by_subscription,
            self.profile_url,
            self.started_at,
            self.subscribed,
            self.current_vacation_started_at,
        )


class Subject(Resource):
    def __init__(self, json_data):
        super().__init__(json_data)
        resource_data = json_data["data"]
        self.level = resource_data["level"]
        self.created_at = parse8601(resource_data["created_at"])
        self.characters = resource_data["characters"]
        self.meanings = [
            Meaning(meaning_json) for meaning_json in resource_data["meanings"]
        ]
        self.document_url = resource_data["document_url"]
        self.hidden_at = resource_data["hidden_at"]


class Radical(Subject):
    resource = "radical"

    def __init__(self, json_data):
        super().__init__(json_data)
        self.character_images = (
            self._resource["character_images"]
            if "character_images" in self._resource.keys()
            else None
        )
        self.amalgamation_subject_ids = self._resource["amalgamation_subject_ids"]


class Vocabulary(Subject):
    resource = "vocabulary"

    def __init__(self, json_data):
        super().__init__(json_data)
        self.parts_of_speech = self._resource["parts_of_speech"]
        self.component_subject_ids = self._resource["component_subject_ids"]
        self.readings = [
            Reading(reading_json) for reading_json in self._resource["readings"]
        ]


class Kanji(Subject):
    resource = "kanji"

    def __init__(self, json_data):
        super().__init__(json_data)
        self.amalgamation_subject_ids = self._resource["amalgamation_subject_ids"]
        self.component_subject_ids = self._resource["component_subject_ids"]
        self.readings = [
            Reading(reading_json) for reading_json in self._resource["readings"]
        ]


class Meaning:
    def __init__(self, meaning_json):
        self.meaning = meaning_json["meaning"]
        self.primary = meaning_json["primary"]
        self.accepted_answer = meaning_json["accepted_answer"]


class Reading:
    def __init__(self, meaning_json):
        self.reading = meaning_json["reading"]
        self.primary = meaning_json["primary"]
        self.accepted_answer = meaning_json["accepted_answer"]


class Assignment(Resource):
    resource = "assignment"

    def __init__(self, json_data):
        super().__init__(json_data)
        self.created_at = parse8601(self._resource["created_at"])
        self.subject_id = self._resource["subject_id"]
        self.subject_type = self._resource["subject_type"]
        self.level = self._resource["level"]
        self.srs_stage = self._resource["srs_stage"]
        self.srs_stage_name = self._resource["srs_stage_name"]
        self.unlocked_at = parse8601(self._resource["unlocked_at"])
        self.started_at = parse8601(self._resource["started_at"])
        self.passed_at = parse8601(self._resource["passed_at"])
        self.burned_at = parse8601(self._resource["burned_at"])
        self.available_at = parse8601(self._resource["available_at"])
        self.resurrected_at_at = parse8601(self._resource["resurrected_at"])
        self.passed = self._resource["passed"]
        self.resurrected = self._resource["resurrected"]
        self.hidden = self._resource["hidden"]


class Reset(Resource):
    resource = "reset"

    def __init__(self, json_data):
        super().__init__(json_data)
        self.created_at = parse8601(self._resource["created_at"])
        self.original_level = self._resource["original_level"]
        self.target_level = self._resource["target_level"]
        self.confirmed_at = parse8601(self._resource["confirmed_at"])


class ReviewStatistic(Resource):
    resource = "review_statistic"

    def __init__(self, json_data):
        super().__init__(json_data)
        self.created_at = parse8601(self._resource["created_at"])
        self.subject_id = self._resource["subject_id"]
        self.subject_type = self._resource["subject_type"]
        self.meaning_correct = self._resource["meaning_correct"]
        self.meaning_incorrect = self._resource["meaning_incorrect"]
        self.meaning_max_streak = self._resource["meaning_max_streak"]
        self.meaning_current_streak = self._resource["meaning_current_streak"]
        self.reading_correct = self._resource["reading_correct"]
        self.reading_incorrect = self._resource["reading_incorrect"]
        self.reading_max_streak = self._resource["reading_max_streak"]
        self.reading_current_streak = self._resource["reading_current_streak"]
        self.percentage_correct = self._resource["percentage_correct"]
        self.hidden = self._resource["hidden"]


class StudyMaterial(Resource):
    resource = "study_material"

    def __init__(self, json_data):
        super().__init__(json_data)
        self.created_at = parse8601(self._resource["created_at"])
        self.subject_id = self._resource["subject_id"]
        self.subject_type = self._resource["subject_type"]
        self.meaning_note = self._resource["meaning_note"]
        self.reading_note = self._resource["reading_note"]
        self.meaning_synonyms = self._resource["meaning_synonyms"]
        self.hidden = self._resource["hidden"]


class Lessons(object):
    def __init__(self, json_data):
        self.subject_ids = json_data["subject_ids"]
        self.available_at = parse8601(json_data["available_at"])


class UpcomingReview(object):
    def __init__(self, json_data):
        self.subject_ids = json_data["subject_ids"]
        self.available_at = parse8601(json_data["available_at"])


class Summary(Resource):
    resource = "report"

    def __init__(self, json_data):
        super().__init__(json_data)
        # Note that there is only ever one lesson object, as per this forum thread https://community.wanikani.com/t/api-v2-alpha-documentation/18987
        self.lessons = Lessons(self._resource["lessons"][0])
        self.next_reviews_at = self._resource["next_reviews_at"]
        self.reviews = [
            UpcomingReview(review_json) for review_json in self._resource["reviews"]
        ]


class Review(Resource):
    resource = "review"

    def __init__(self, json_data):
        super().__init__(json_data)
        self.created_at = parse8601(self._resource["created_at"])
        self.assignment_id = self._resource["assignment_id"]
        self.subject_id = self._resource["subject_id"]
        self.starting_srs_stage = self._resource["starting_srs_stage"]
        self.starting_srs_stage_name = self._resource["starting_srs_stage_name"]
        self.ending_srs_stage = self._resource["ending_srs_stage"]
        self.ending_srs_stage_name = self._resource["ending_srs_stage_name"]
        self.incorrect_meaning_answers = self._resource["incorrect_meaning_answers"]
        self.incorrect_reading_answers = self._resource["incorrect_reading_answers"]


class LevelProgression(Resource):
    resource = "level_progression"

    def __init__(self, json_data):
        super().__init__(json_data)
        self.created_at = parse8601(self._resource["created_at"])
        self.level = self._resource["level"]
        self.unlocked_at = parse8601(self._resource["unlocked_at"])
        self.started_at = parse8601(self._resource["started_at"])
        self.passed_at = parse8601(self._resource["passed_at"])
        self.completed_at = parse8601(self._resource["completed_at"])


def parse8601(time_field):
    if time_field:
        return dateutil.parser.parse(time_field)
    else:
        return None


resources = {
    UserInformation.resource: UserInformation,
    Assignment.resource: Assignment,
    Review.resource: Review,
    ReviewStatistic.resource: ReviewStatistic,
    LevelProgression.resource: LevelProgression,
    StudyMaterial.resource: StudyMaterial,
    Reset.resource: Reset,
    Kanji.resource: Kanji,
    Vocabulary.resource: Vocabulary,
    Radical.resource: Radical,
    Summary.resource: Summary,
    Page.resource: Page,
}


def factory(resource_json):
    try:
        return resources[resource_json["object"]](resource_json)
    except KeyError:
        raise UnknownResourceException(
            "We have no clue how to handle resource of type: {}".format(
                resource_json["object"]
            )
        )
