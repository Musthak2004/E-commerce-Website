from django.test import TestCase


class ErrorHandlerTests(TestCase):
    def test_404_renders_custom_template(self):
        resp = self.client.get("/nonexistent-page/")
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed(resp, "errors/404.html")

    def test_403_redirects_non_staff(self):
        resp = self.client.get("/admin/dashboard/")
        self.assertRedirects(resp, "/admin/login/?next=/admin/dashboard/")
