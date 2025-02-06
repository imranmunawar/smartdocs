from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse

from ..models import Category, Template
from ..services.category import CategoryService
from ..services.template import TemplateService
from ..utils.access import get_user_access_levels

@login_required
def category_list(request):
    """
    Display root level categories
    """
    category_service = CategoryService()
    
    try:
        root_categories = category_service.get_root_categories()
        
        context = {
            'categories': root_categories,
            'category_count': len(root_categories)
        }
        return render(request, 'categories/list.html', context)
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
        return redirect('dashboard')

@login_required
def category_detail(request, category_id: int):
    """
    Display category details with subcategories and templates
    
    Args:
        category_id (int): ID of the category to display
    """
    category_service = CategoryService()
    template_service = TemplateService()
    
    try:
        # Get category details
        category_details = category_service.get_category_details(category_id)
        if not category_details:
            raise ValueError("Category not found")
            
        # Get subcategories
        subcategories = category_service.get_subcategories(category_id)
        
        # Get category hierarchy
        category_hierarchy = category_service.get_category_breadcrumb(category_id)
        
        # Get available templates based on user access
        user_access_levels = get_user_access_levels(request.user)
        available_templates = template_service.get_available_templates(
            category_id=category_id,
            user_access_levels=user_access_levels,
            is_admin=request.user.is_staff
        )
        
        context = {
            'category': category_details,
            'subcategories': subcategories,
            'category_hierarchy': category_hierarchy,
            'templates': available_templates,
            'subcategory_count': len(subcategories),
            'template_count': len(available_templates)
        }
        return render(request, 'categories/detail.html', context)
        
    except Exception as e:
        messages.error(request, str(e))
        return redirect('category_list')

class CategoryHierarchyService:
    """Service class for handling category hierarchy operations"""
    
    @staticmethod
    def build_category_hierarchy(category: Category) -> list:
        """
        Build hierarchical path from root to given category
        
        Args:
            category (Category): Category to build hierarchy for
            
        Returns:
            list: List of categories from root to target category
        """
        hierarchy = []
        current = category
        
        # Build path from current category up to root
        while current:
            hierarchy.append(current)
            current = current.parent_category
            
        # Reverse to get root->leaf order
        hierarchy.reverse()
        return hierarchy

    @staticmethod
    def get_category_children(category: Category) -> list:
        """
        Get immediate child categories
        
        Args:
            category (Category): Parent category
            
        Returns:
            list: List of child categories
        """
        return category.children.all().order_by('sequence_id')

    @staticmethod
    def get_category_templates(category: Category, user_access_levels: list) -> list:
        """
        Get templates available for category based on access levels
        
        Args:
            category (Category): Category to get templates for
            user_access_levels (list): List of user's access levels
            
        Returns:
            list: List of available templates
        """
        template_query = Template.objects.filter(
            category=category,
            is_active=True
        )
        
        if user_access_levels:
            template_query = template_query.filter(
                access_level__in=user_access_levels
            )
            
        return template_query.order_by('sequence_id')
