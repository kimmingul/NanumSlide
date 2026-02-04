"""이미지 검색 및 생성 서비스"""

import httpx
from typing import Optional
from openai import OpenAI
from src.config import get_settings, ImageProvider


async def search_image(query: str, per_page: int = 1) -> Optional[str]:
    """
    이미지 검색 또는 생성하여 URL 반환

    Args:
        query: 검색 키워드 또는 이미지 생성 프롬프트 (영문 권장)
        per_page: 검색 결과 수 (검색 API 전용)

    Returns:
        이미지 URL 또는 None
    """
    settings = get_settings()

    if settings.image_provider == ImageProvider.DISABLED:
        return None

    if settings.image_provider == ImageProvider.DALLE:
        return await _generate_dalle_image(query, settings.openai_api_key)
    elif settings.image_provider == ImageProvider.PEXELS:
        return await _search_pexels(query, settings.pexels_api_key, per_page)
    elif settings.image_provider == ImageProvider.PIXABAY:
        return await _search_pixabay(query, settings.pixabay_api_key, per_page)

    return None


async def _generate_dalle_image(prompt: str, api_key: Optional[str]) -> Optional[str]:
    """DALL-E로 이미지 생성"""
    if not api_key:
        print("OpenAI API 키가 설정되지 않았습니다.")
        return None

    try:
        import asyncio

        def sync_call():
            client = OpenAI(api_key=api_key)
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1792x1024",  # 프레젠테이션에 적합한 가로형
                quality="standard",
                n=1,
            )
            return response.data[0].url

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_call)
    except Exception as e:
        print(f"DALL-E 이미지 생성 실패: {e}")
        return None


async def _search_pexels(query: str, api_key: Optional[str], per_page: int = 1) -> Optional[str]:
    """Pexels API로 이미지 검색"""
    if not api_key:
        print("Pexels API 키가 설정되지 않았습니다.")
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": api_key},
                params={
                    "query": query,
                    "per_page": per_page,
                    "orientation": "landscape",
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("photos"):
                    # medium 사이즈 이미지 URL 반환
                    return data["photos"][0]["src"]["medium"]
            else:
                print(f"Pexels API 오류: {response.status_code}")
    except Exception as e:
        print(f"Pexels 이미지 검색 실패: {e}")

    return None


async def _search_pixabay(query: str, api_key: Optional[str], per_page: int = 1) -> Optional[str]:
    """Pixabay API로 이미지 검색"""
    if not api_key:
        print("Pixabay API 키가 설정되지 않았습니다.")
        return None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://pixabay.com/api/",
                params={
                    "key": api_key,
                    "q": query,
                    "per_page": per_page,
                    "image_type": "photo",
                    "orientation": "horizontal",
                },
                timeout=10.0,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("hits"):
                    # webformat 이미지 URL 반환
                    return data["hits"][0]["webformatURL"]
            else:
                print(f"Pixabay API 오류: {response.status_code}")
    except Exception as e:
        print(f"Pixabay 이미지 검색 실패: {e}")

    return None


async def fetch_images_for_slides(slides_data: list[dict]) -> list[dict]:
    """
    슬라이드 목록에 대해 이미지 검색 및 URL 추가

    Args:
        slides_data: 슬라이드 데이터 목록 (image_prompt 포함)

    Returns:
        image_url이 추가된 슬라이드 데이터 목록
    """
    for slide in slides_data:
        image_prompt = slide.get("image_prompt")
        if image_prompt:
            image_url = await search_image(image_prompt)
            if image_url:
                slide["image_url"] = image_url

    return slides_data
