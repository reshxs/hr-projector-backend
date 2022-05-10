import typing as tp

from django.db.models import QuerySet
from pydantic import Field, BaseModel
from pydantic.generics import GenericModel
from pydantic.main import ModelMetaclass

_ItemsT = tp.TypeVar('_ItemsT')


class PaginationParams(BaseModel):
    page: int = Field(1, title='Страница', ge=1)
    per_page: int = Field(10, title='Лимит объектов в списке', ge=1, le=100)
    count: bool = Field(
        False,
        title='Подсчитать количество доступных объектов и вернуть с ответом',
    )


class PaginationInfinityScrollParams(BaseModel):
    offset: int = Field(
        0,
        title='Смещение (сколько объектов пропустить)',
        ge=0,
    )
    limit: int = Field(
        10,
        title='Сколько объектов вернуть (макс.)',
        gt=0,
        example=10,
    )
    count: bool = Field(
        False,
        title='Подсчитать количество доступных объектов и вернуть с ответом',
    )


AnyPagination = tp.Union[PaginationParams, PaginationInfinityScrollParams]


class BasePaginatedResponse(GenericModel):
    has_next: tp.Optional[bool] = Field(..., title='Есть ли еще объекты')
    total_size: tp.Optional[int] = Field(
        title='Всего объектов',
        example=100,
        description='Может быть null или отсутствовать, если запрос был сделан с count=false',
    )


class PaginatedResponse(BasePaginatedResponse, tp.Generic[_ItemsT]):
    items: list[_ItemsT] = Field(..., title='Объекты')


_ST = tp.TypeVar('_ST')  # Schema Type


class TypedPaginator(tp.Generic[_ST]):
    def __init__(self, schema: tp.Type[_ST], query: QuerySet):
        self.schema = schema
        self.query = query
        self._check_query_is_ordered()

    def get_response(
        self,
        pagination: tp.Union[PaginationParams, PaginationInfinityScrollParams],
        *model_args: tp.Iterable[tp.Any],
        **model_kwargs: tp.Any,
    ) -> PaginatedResponse[_ST]:
        """Получить ответ в соответствии с переданной навигацией

        :param pagination: правила пагинации
        :param model_args: доп. аргументы для метода `.from_model`
        :param model_kwargs: доп. аргументы для метода `.from_model`
        :return: ответ с постраничной навигацией
        """
        total_size = None

        if isinstance(pagination, PaginationParams):
            bottom = (pagination.page - 1) * pagination.per_page
            top = bottom + pagination.per_page
        else:
            assert isinstance(pagination, PaginationInfinityScrollParams)
            bottom = pagination.offset
            top = pagination.offset + pagination.limit

        orphans = 1
        items = [self.schema.from_model(o, *model_args, **model_kwargs) for o in self.query[bottom : top + orphans]]

        has_next = len(items) > (top - bottom)
        if has_next:
            # Удаляем вычитанные orphans объекты
            items = items[:-orphans]

        if pagination.count:
            total_size = self.query.count()

        return PaginatedResponse[self.schema](
            items=items,
            has_next=has_next,
            total_size=total_size,
        )

    def _check_query_is_ordered(self):
        """
        Warn if self.query is unordered (typically a QuerySet).
        """
        ordered = getattr(self.query, 'ordered', None)
        if ordered is not None and not ordered:
            obj_list_repr = (
                '{} {}'.format(self.query.model, self.query.__class__.__name__)
                if hasattr(self.query, 'model')
                else '{!r}'.format(self.query)
            )


class TypedPaginatorWithCustomParams(TypedPaginator):
    def __init__(self, schema: tp.Type[_ST], query: QuerySet, paginated_response: tp.Any):
        assert isinstance(
            paginated_response, ModelMetaclass
        ), 'paginated_response должен наследоваться от pydantic.generics.GenericModel'
        super().__init__(schema, query)
        self._custom_params = {}
        self._paginated_response = paginated_response

    def set_custom_params(self, custom_params: tp.Dict[str, tp.Any]):
        """Параметры для добавления к основным.

        **custom_params подставляются в query.aggregate
        """
        assert isinstance(custom_params, dict)
        for param in custom_params.keys():
            assert (
                param in self._paginated_response.__fields__
            ), 'custom_params должны соответствовать paginated_response'
        self._custom_params = custom_params

    def _get_custom_params(self) -> tp.Dict[str, tp.Any]:
        return self.query.aggregate(**self._custom_params)

    def get_response(
        self,
        pagination: tp.Union[PaginationParams, PaginationInfinityScrollParams],
        *model_args: tp.Iterable[tp.Any],
    ) -> tp.Any:
        """Получить ответ в соответствии с переданной навигацией

        :param pagination: правила пагинации
        :param model_args: доп. аргументы для метода `.from_model`
        :return: ответ с постраничной навигацией
        """
        total_size = None

        if isinstance(pagination, PaginationParams):
            bottom = (pagination.page - 1) * pagination.per_page
            top = bottom + pagination.per_page
        else:
            assert isinstance(pagination, PaginationInfinityScrollParams)
            bottom = pagination.offset
            top = pagination.offset + pagination.limit

        if self._custom_params:
            custom_params = self._get_custom_params()
        else:
            custom_params = self._custom_params

        orphans = 1
        items = [self.schema.from_model(o, *model_args) for o in self.query[bottom : top + orphans]]

        has_next = len(items) > (top - bottom)
        if has_next:
            # Удаляем вычитанные orphans объекты
            items = items[:-orphans]

        if 'total_size' in custom_params:
            total_size = custom_params.pop('total_size')
        elif pagination.count:
            total_size = self.query.count()

        return self._paginated_response[self.schema](
            items=items,
            has_next=has_next,
            total_size=total_size,
            **custom_params,
        )
