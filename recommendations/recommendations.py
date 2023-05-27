from concurrent import futures
import random

import grpc
import recommendations_pb2_grpc
from recommendations_pb2 import RecommendationResponse, BookRecommendation, BookCategory
from grpc_interceptor import ExceptionToStatusInterceptor
from grpc_interceptor.exceptions import NotFound

books_by_category = {
    BookCategory.SCIENCE_FICTION: [
        BookRecommendation(id=1, title='The Three-Body Problem'),
        BookRecommendation(id=2, title='The Dark Forest'),
        BookRecommendation(id=3, title='Death\'s End'),
    ],
    BookCategory.MYSTERY: [
        BookRecommendation(id=4, title='The Cuckoo\'s Calling'),
        BookRecommendation(id=5, title='The Silkworm'),
        BookRecommendation(id=6, title='Career of Evil'),
    ],
    BookCategory.SELF_HELP: [
        BookRecommendation(
            id=7, title='The 7 Habits of Highly Effective People'),
        BookRecommendation(
            id=8, title='How to Win Friends and Influence People'),
        BookRecommendation(id=9, title='Think and Grow Rich'),
    ],
}


class RecommendationService(recommendations_pb2_grpc.RecommendationsServicer):

    def Recommend(self, request, context):
        if request.category not in books_by_category:
            raise NotFound("Category not found")

        books_for_category = books_by_category[request.category]
        num_results = min(len(books_for_category), request.max_results)

        books_to_recommend = random.sample(books_for_category, num_results)

        return RecommendationResponse(books=books_to_recommend)


def serve():
    interceptors = [ExceptionToStatusInterceptor()]
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=interceptors
    )
    recommendations_pb2_grpc.add_RecommendationsServicer_to_server(
        RecommendationService(), server
    )

    with open("server.key", "rb") as fp:
        server_key = fp.read()
    with open("server.pem", "rb") as fp:
        server_cert = fp.read()
    with open("ca.pem", "rb") as fp:
        ca_cert = fp.read()

    creds = grpc.ssl_server_credentials(
        [(server_key, server_cert)],
        root_certificates=ca_cert,
        require_client_auth=True,
    )

    server.add_secure_port("[::]:443", creds)
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
