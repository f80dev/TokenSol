import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AutovalidateComponent } from './autovalidate.component';

describe('AutovalidateComponent', () => {
  let component: AutovalidateComponent;
  let fixture: ComponentFixture<AutovalidateComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ AutovalidateComponent ]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AutovalidateComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
